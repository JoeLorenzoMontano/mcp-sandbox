import os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import httpx
import json
from typing import List, Dict, Any, Optional
import logging
import asyncio
from dotenv import load_dotenv

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
            
            # Send the request to the MCP server
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{mcp_server}/v1/chat",
                    json=mcp_request.dict(),
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    logger.error(f"MCP server error: {response.status_code} - {response.text}")
                    raise HTTPException(status_code=response.status_code, detail=f"Error from MCP server for step {step.name}")
                
                mcp_response = response.json()
            
            # Extract the text response
            step_result = {
                "step_name": step.name,
                "mcp_server": mcp_server,
                "response": mcp_response
            }
            results.append(step_result)
            
            # Update the context for the next step
            response_text = ""
            for part in mcp_response.get("message", {}).get("content", {}).get("parts", []):
                if part.get("type") == "text":
                    response_text += part.get("text", "")
            
            current_context = response_text
            
            logger.info(f"Completed step {i+1}: {step.name}")
            
        logger.info("Workflow completed successfully")
        return WorkflowResponse(results=results)
        
    except Exception as e:
        logger.error(f"Error processing workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/v1/mcp-servers")
async def list_mcp_servers():
    servers = [MCP_SERVER_URL] + EXTERNAL_MCP_SERVERS
    return {"servers": servers}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)