import os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import httpx
import json
from typing import List, Dict, Any, Optional
import logging
import asyncio
from dotenv import load_dotenv

# Import Smithery client module
from smithery_client import connect_to_smithery, call_smithery_agent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("workflow_orchestrator")

# MCP Server URL
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcp_server:8000")

# External MCP Servers (comma-separated list)
EXTERNAL_MCP_SERVERS = [
    server.strip() for server in os.getenv("EXTERNAL_MCP_SERVERS", "").split(",") 
    if server.strip()
]

# Smithery.ai Configuration
SMITHERY_API_KEY = os.getenv("SMITHERY_API_KEY", "")
SMITHERY_REGISTRY_URL = os.getenv("SMITHERY_REGISTRY_URL", "https://registry.smithery.ai")
SMITHERY_ENABLED = bool(SMITHERY_API_KEY)

app = FastAPI(title="Workflow Orchestrator")

# MCP and Workflow Schemas
class MCPContent(BaseModel):
    content_type: str
    parts: List[Dict[str, Any]]

class MCPMessage(BaseModel):
    role: str
    content: MCPContent

class MCPRequest(BaseModel):
    messages: List[MCPMessage]
    tools: Optional[List[Dict[str, Any]]] = None

class MCPResponse(BaseModel):
    message: MCPMessage

class WorkflowStep(BaseModel):
    name: str
    mcp_server: Optional[str] = None  # If None, use default server
    role: str = "user"  # "user" or "system"
    messages: List[Dict[str, Any]] = []
    tools: Optional[List[Dict[str, Any]]] = None
    # Smithery.ai specific fields
    smithery_agent_id: Optional[str] = None
    smithery_params: Optional[Dict[str, Any]] = None
    
class WorkflowRequest(BaseModel):
    steps: List[WorkflowStep]
    input: str

class WorkflowResponse(BaseModel):
    results: List[Dict[str, Any]]

@app.get("/")
async def read_root():
    return {"status": "healthy", "service": "Workflow Orchestrator"}

@app.post("/v1/workflow", response_model=WorkflowResponse)
async def run_workflow(request: WorkflowRequest):
    logger.info(f"Received workflow request with {len(request.steps)} steps")
    
    results = []
    current_context = request.input
    
    try:
        for i, step in enumerate(request.steps):
            logger.info(f"Executing workflow step {i+1}: {step.name}")
            
            # Check if this step uses a Smithery agent
            if step.smithery_agent_id:
                if not SMITHERY_ENABLED:
                    logger.error("Smithery is not enabled (API key not configured)")
                    raise HTTPException(status_code=400, detail="Smithery integration is not enabled")
                
                logger.info(f"Using Smithery agent for step {step.name}: {step.smithery_agent_id}")
                
                try:
                    # Call the Smithery agent directly using WebSockets
                    smithery_response = await call_smithery_agent(
                        agent_id=step.smithery_agent_id,
                        prompt=current_context,
                        params=step.smithery_params
                    )
                    
                    step_result = {
                        "step_name": step.name,
                        "mcp_server": f"smithery:{step.smithery_agent_id}",
                        "response": {
                            "message": {
                                "role": "assistant",
                                "content": {
                                    "content_type": "multimodal/html",
                                    "parts": [
                                        {
                                            "type": "text",
                                            "text": smithery_response["response"]
                                        }
                                    ]
                                }
                            }
                        },
                        "smithery_response": smithery_response
                    }
                    
                    # Update the context with the Smithery response
                    current_context = smithery_response["response"]
                    
                except Exception as smithery_error:
                    logger.error(f"Smithery agent error: {str(smithery_error)}")
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Error from Smithery agent for step {step.name}: {str(smithery_error)}"
                    )
            else:
                # Regular MCP server flow
                # Determine which MCP server to use
                mcp_server = step.mcp_server or MCP_SERVER_URL
                
                # Format the MCP request
                messages = []
                
                # Add any predefined messages from the step
                for msg in step.messages:
                    messages.append(MCPMessage(
                        role=msg.get("role", "system"),
                        content=MCPContent(
                            content_type=msg.get("content_type", "multimodal/html"),
                            parts=[{"type": "text", "text": msg.get("content", "")}]
                        )
                    ))
                
                # Add the current context as a new message
                messages.append(MCPMessage(
                    role=step.role,
                    content=MCPContent(
                        content_type="multimodal/html",
                        parts=[{"type": "text", "text": current_context}]
                    )
                ))
                
                # Create the MCP request
                mcp_request = MCPRequest(
                    messages=messages,
                    tools=step.tools
                )
                
                # Prepare headers for the request
                headers = {}
                
                # Check if this is a Smithery.ai server
                if SMITHERY_ENABLED and SMITHERY_REGISTRY_URL in mcp_server:
                    logger.info(f"Using Smithery.ai authentication for {mcp_server}")
                    headers["Authorization"] = f"Bearer {SMITHERY_API_KEY}"
                
                # Send the request to the MCP server
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{mcp_server}/v1/chat",
                        json=mcp_request.dict(),
                        headers=headers,
                        timeout=60.0
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"MCP server error: {response.status_code} - {response.text}")
                        raise HTTPException(
                            status_code=response.status_code, 
                            detail=f"Error from MCP server for step {step.name}"
                        )
                    
                    mcp_response = response.json()
                
                # Extract the text response
                step_result = {
                    "step_name": step.name,
                    "mcp_server": mcp_server,
                    "response": mcp_response
                }
                
                # Update the context for the next step
                response_text = ""
                for part in mcp_response.get("message", {}).get("content", {}).get("parts", []):
                    if part.get("type") == "text":
                        response_text += part.get("text", "")
                
                current_context = response_text
            
            # Add the result to our results list
            results.append(step_result)
            logger.info(f"Completed step {i+1}: {step.name}")
            
        logger.info("Workflow completed successfully")
        return WorkflowResponse(results=results)
        
    except Exception as e:
        logger.error(f"Error processing workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def fetch_smithery_registry():
    """Fetch available MCP servers from Smithery.ai registry"""
    if not SMITHERY_ENABLED:
        return []
        
    try:
        headers = {"Authorization": f"Bearer {SMITHERY_API_KEY}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SMITHERY_REGISTRY_URL}/agents",
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code != 200:
                logger.error(f"Smithery registry error: {response.status_code} - {response.text}")
                return []
                
            registry_data = response.json()
            
            # Extract MCP server URLs from the registry data
            # Format may vary - adjust parsing based on actual Smithery API response
            smithery_servers = []
            for agent in registry_data.get("agents", []):
                if "endpoint" in agent:
                    smithery_servers.append(agent["endpoint"])
                    
            return smithery_servers
            
    except Exception as e:
        logger.error(f"Error fetching Smithery registry: {str(e)}")
        return []

@app.get("/v1/mcp-servers")
async def list_mcp_servers():
    # Start with local and configured external servers
    servers = [MCP_SERVER_URL] + EXTERNAL_MCP_SERVERS
    
    # Add Smithery servers if enabled
    if SMITHERY_ENABLED:
        smithery_servers = await fetch_smithery_registry()
        servers.extend(smithery_servers)
        
    return {"servers": servers}

class SmitheryTestRequest(BaseModel):
    agent_id: str
    prompt: str
    params: Optional[Dict[str, Any]] = None

@app.post("/v1/test-smithery")
async def test_smithery_connection(request: SmitheryTestRequest):
    """Test connection to a Smithery.ai agent"""
    if not SMITHERY_ENABLED:
        raise HTTPException(status_code=400, detail="Smithery integration is not enabled")
    
    try:
        logger.info(f"Testing connection to Smithery agent: {request.agent_id}")
        response = await call_smithery_agent(
            agent_id=request.agent_id,
            prompt=request.prompt,
            params=request.params
        )
        return response
    except Exception as e:
        logger.error(f"Error testing Smithery connection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Smithery connection error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)