import os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import httpx
import json
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_server")

# Configure Ollama settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:latest")

app = FastAPI(title="MCP Server")

# MCP Message Schemas
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

@app.get("/")
async def read_root():
    return {"status": "healthy", "service": "MCP Server"}

@app.post("/v1/chat", response_model=MCPResponse)
async def chat(request: MCPRequest):
    logger.info(f"Received MCP request with {len(request.messages)} messages")
    
    try:
        # Format the messages for Ollama
        formatted_messages = []
        for msg in request.messages:
            # Extract text from the MCP message format
            text_parts = []
            for part in msg.content.parts:
                if part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
            
            formatted_messages.append({
                "role": msg.role,
                "content": " ".join(text_parts)
            })
        
        # Prepare the request for Ollama
        ollama_request = {
            "model": OLLAMA_MODEL,
            "messages": formatted_messages,
            "stream": False
        }
        
        # If tools are provided, format them for Ollama
        if request.tools:
            ollama_request["tools"] = request.tools
        
        # Call the Ollama API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=ollama_request,
                timeout=60.0
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Error from model provider")
            
            ollama_response = response.json()
            
        # Convert the response back to MCP format
        mcp_response = MCPResponse(
            message=MCPMessage(
                role="assistant",
                content=MCPContent(
                    content_type="multimodal/html",
                    parts=[
                        {
                            "type": "text",
                            "text": ollama_response.get("message", {}).get("content", "")
                        }
                    ]
                )
            )
        )
        
        logger.info("Successfully processed request")
        return mcp_response
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)