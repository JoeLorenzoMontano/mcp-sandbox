import os
import logging
import smithery
import mcp
from mcp.client.websocket import websocket_client
from typing import Dict, Any, Optional, List

# Configure logging
logger = logging.getLogger("smithery_client")

# Get Smithery API key from environment
SMITHERY_API_KEY = os.getenv("SMITHERY_API_KEY", "")


async def connect_to_smithery(agent_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Connect to a Smithery.ai agent using WebSockets.
    
    Args:
        agent_id (str): The Smithery agent ID (e.g. "@turkyden/weather")
        params (Dict[str, Any], optional): Parameters to pass to the Smithery agent
    
    Returns:
        Dict[str, Any]: The response from the Smithery agent
    """
    if not SMITHERY_API_KEY:
        logger.error("SMITHERY_API_KEY environment variable is not set")
        raise ValueError("SMITHERY_API_KEY environment variable is not set")
    
    if not agent_id:
        logger.error("Agent ID is required")
        raise ValueError("Agent ID is required")
    
    # If agent_id doesn't start with @, add it
    if not agent_id.startswith("@"):
        agent_id = f"@{agent_id}"
    
    # If agent_id doesn't contain a slash, assume it's a user and add a placeholder agent name
    if "/" not in agent_id:
        logger.warning(f"Agent ID {agent_id} doesn't contain a slash. Adding placeholder agent name.")
        agent_id = f"{agent_id}/agent"
    
    # Create a URL safe params object or empty dict if none provided
    safe_params = params or {}
    
    # Create Smithery URL with server endpoint
    agent_path = agent_id.lstrip("@")
    url = smithery.create_smithery_url(f"wss://server.smithery.ai/{agent_path}/ws", safe_params)
    
    # Add API key to URL
    url = f"{url}&api_key={SMITHERY_API_KEY}"
    
    logger.info(f"Connecting to Smithery agent: {agent_id}")
    
    try:
        # Connect to the server using websocket client
        async with websocket_client(url) as streams:
            async with mcp.ClientSession(*streams) as session:
                # List available tools
                tools_result = await session.list_tools()
                available_tools = [t.name for t in tools_result]
                logger.info(f"Available tools from Smithery agent: {', '.join(available_tools)}")
                
                # Return the session info and available tools
                return {
                    "status": "connected",
                    "agent_id": agent_id,
                    "available_tools": available_tools
                }
    except Exception as e:
        logger.error(f"Error connecting to Smithery agent {agent_id}: {str(e)}")
        raise
        

async def call_smithery_agent(agent_id: str, prompt: str, 
                              params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Call a Smithery.ai agent with a prompt and get a response.
    
    Args:
        agent_id (str): The Smithery agent ID (e.g. "@turkyden/weather")
        prompt (str): The prompt to send to the agent
        params (Dict[str, Any], optional): Parameters to pass to the Smithery agent
    
    Returns:
        Dict[str, Any]: The response from the Smithery agent
    """
    if not SMITHERY_API_KEY:
        logger.error("SMITHERY_API_KEY environment variable is not set")
        raise ValueError("SMITHERY_API_KEY environment variable is not set")
    
    if not agent_id:
        logger.error("Agent ID is required")
        raise ValueError("Agent ID is required")
    
    if not prompt:
        logger.error("Prompt is required")
        raise ValueError("Prompt is required")
    
    # If agent_id doesn't start with @, add it
    if not agent_id.startswith("@"):
        agent_id = f"@{agent_id}"
    
    # If agent_id doesn't contain a slash, assume it's a user and add a placeholder agent name
    if "/" not in agent_id:
        logger.warning(f"Agent ID {agent_id} doesn't contain a slash. Adding placeholder agent name.")
        agent_id = f"{agent_id}/agent"
    
    # Create a URL safe params object or empty dict if none provided
    safe_params = params or {}
    
    # Create Smithery URL with server endpoint
    agent_path = agent_id.lstrip("@")
    url = smithery.create_smithery_url(f"wss://server.smithery.ai/{agent_path}/ws", safe_params)
    
    # Add API key to URL
    url = f"{url}&api_key={SMITHERY_API_KEY}"
    
    logger.info(f"Connecting to Smithery agent: {agent_id}")
    
    try:
        # Connect to the server using websocket client
        async with websocket_client(url) as streams:
            async with mcp.ClientSession(*streams) as session:
                # List available tools
                tools_result = await session.list_tools()
                available_tools = [t.name for t in tools_result]
                logger.info(f"Available tools: {', '.join(available_tools)}")
                
                # Send the prompt to the agent
                logger.info(f"Sending prompt to agent: {prompt[:50]}...")
                
                # Create an MCP message with the prompt
                message = mcp.Message(
                    role="user",
                    content=mcp.Content(
                        content_type="text",
                        parts=[
                            mcp.Part(
                                type="text", 
                                text=prompt
                            )
                        ]
                    )
                )
                
                # Send the message and get a response
                response = await session.send_message(message)
                
                # Extract text from the response
                response_text = ""
                for part in response.content.parts:
                    if part.type == "text":
                        response_text += part.text
                
                return {
                    "status": "success",
                    "agent_id": agent_id,
                    "response": response_text,
                    "raw_response": response.dict()
                }
    except Exception as e:
        logger.error(f"Error calling Smithery agent {agent_id}: {str(e)}")
        raise