import os
import logging
import traceback
import json
import smithery
import mcp
from mcp.client.websocket import websocket_client
from typing import Dict, Any, Optional, List, Union

# Configure logging
logger = logging.getLogger("smithery_client")

# Get Smithery API key from environment
SMITHERY_API_KEY = os.getenv("SMITHERY_API_KEY", "")


async def connect_to_smithery(agent_id: str, params: Optional[Dict[str, Any]] = None, 
                              api_key: Optional[str] = None, debug: bool = False) -> Dict[str, Any]:
    """
    Connect to a Smithery.ai agent using WebSockets.
    
    Args:
        agent_id (str): The Smithery agent ID (e.g. "@turkyden/weather")
        params (Dict[str, Any], optional): Parameters to pass to the Smithery agent
        api_key (str, optional): Override the environment API key
        debug (bool, optional): Enable debug logging
    
    Returns:
        Dict[str, Any]: The response from the Smithery agent
    """
    if debug:
        # Set logging to DEBUG level
        logger.setLevel(logging.DEBUG)
        # Set mcp logger to DEBUG level
        mcp_logger = logging.getLogger("mcp")
        mcp_logger.setLevel(logging.DEBUG)
        # Set smithery logger to DEBUG level
        smithery_logger = logging.getLogger("smithery")
        smithery_logger.setLevel(logging.DEBUG)
    
    # Use provided API key or get from environment
    api_key = api_key or SMITHERY_API_KEY
    
    if not api_key:
        logger.error("No API key provided and SMITHERY_API_KEY not set in environment")
        raise ValueError("Smithery API key is required but not provided")
    
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
    
    try:
        # Create Smithery URL with server endpoint
        logger.info(f"Creating Smithery URL for agent: {agent_id}")
        agent_path = agent_id.lstrip("@")
        url = smithery.create_smithery_url(f"wss://server.smithery.ai/{agent_path}/ws", safe_params)
        
        # Add API key to URL
        url = f"{url}&api_key={api_key}"
        logger.debug(f"URL (without API key): {url.split('&api_key=')[0]}")
    except Exception as e:
        logger.error(f"Error creating Smithery URL: {e}")
        logger.error(traceback.format_exc())
        raise ValueError(f"Failed to create Smithery URL: {e}")
    
    logger.info(f"Connecting to Smithery agent: {agent_id}")
    
    try:
        # Connect to the server using websocket client
        logger.info("Opening WebSocket connection...")
        async with websocket_client(url) as streams:
            logger.info("WebSocket connection established, creating MCP client session...")
            async with mcp.ClientSession(*streams) as session:
                # List available tools
                logger.info("Listing available tools...")
                tools_result = await session.list_tools()
                
                # Handle the ListToolsResult format from the MCP API
                if tools_result:
                    logger.debug(f"Tools result type: {type(tools_result)}")
                    logger.debug(f"Tools result: {tools_result}")
                    
                    # Extract tools from the ListToolsResult
                    available_tools = []
                    
                    # Check if it has a 'tools' attribute (most likely case based on the debug output)
                    if hasattr(tools_result, 'tools') and tools_result.tools:
                        for tool in tools_result.tools:
                            if hasattr(tool, 'name'):
                                available_tools.append(tool.name)
                            elif isinstance(tool, dict) and 'name' in tool:
                                available_tools.append(tool['name'])
                    # Fall back to other formats if needed
                    elif isinstance(tools_result, list):
                        for tool in tools_result:
                            if hasattr(tool, 'name'):
                                available_tools.append(tool.name)
                            elif isinstance(tool, dict) and 'name' in tool:
                                available_tools.append(tool['name'])
                    elif isinstance(tools_result, tuple):
                        # If it's a tuple, try to convert to strings
                        available_tools = [str(t) for t in tools_result]
                    
                    # Display the results
                    if available_tools:
                        logger.info(f"Available tools from Smithery agent: {', '.join(available_tools)}")
                    else:
                        logger.warning("Could not extract tool names from result")
                        logger.warning(f"Raw tools result: {tools_result}")
                        logger.info("Available tools from Smithery agent: (none extracted)")
                else:
                    logger.info("No tools available from Smithery agent")
                    available_tools = []
                
                # Return the session info and available tools
                return {
                    "status": "connected",
                    "agent_id": agent_id,
                    "available_tools": available_tools
                }
    except Exception as e:
        logger.error(f"Error connecting to Smithery agent {agent_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise
        

async def call_smithery_agent(agent_id: str, prompt: str, 
                              params: Optional[Dict[str, Any]] = None,
                              api_key: Optional[str] = None,
                              debug: bool = False,
                              tool_call: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Call a Smithery.ai agent with a prompt and get a response.
    
    Args:
        agent_id (str): The Smithery agent ID (e.g. "@turkyden/weather")
        prompt (str): The prompt to send to the agent
        params (Dict[str, Any], optional): Parameters to pass to the Smithery agent
        api_key (str, optional): Override the environment API key
        debug (bool, optional): Enable debug logging
        tool_call (Dict[str, Any], optional): If provided, calls a specific tool instead of sending a message
                                             Format: {"name": "tool-name", "parameters": {...}}
    
    Returns:
        Dict[str, Any]: The response from the Smithery agent
    """
    if debug:
        # Set logging to DEBUG level
        logger.setLevel(logging.DEBUG)
        # Set mcp logger to DEBUG level
        mcp_logger = logging.getLogger("mcp")
        mcp_logger.setLevel(logging.DEBUG)
        # Set smithery logger to DEBUG level
        smithery_logger = logging.getLogger("smithery")
        smithery_logger.setLevel(logging.DEBUG)
    
    # Use provided API key or get from environment
    api_key = api_key or SMITHERY_API_KEY
    
    if not api_key:
        logger.error("No API key provided and SMITHERY_API_KEY not set in environment")
        raise ValueError("Smithery API key is required but not provided")
    
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
    
    try:
        # Create Smithery URL with server endpoint
        logger.info(f"Creating Smithery URL for agent: {agent_id}")
        agent_path = agent_id.lstrip("@")
        url = smithery.create_smithery_url(f"wss://server.smithery.ai/{agent_path}/ws", safe_params)
        
        # Add API key to URL
        url = f"{url}&api_key={api_key}"
        logger.debug(f"URL (without API key): {url.split('&api_key=')[0]}")
    except Exception as e:
        logger.error(f"Error creating Smithery URL: {e}")
        logger.error(traceback.format_exc())
        raise ValueError(f"Failed to create Smithery URL: {e}")
    
    logger.info(f"Connecting to Smithery agent: {agent_id}")
    
    try:
        # Connect to the server using websocket client
        logger.info("Opening WebSocket connection...")
        async with websocket_client(url) as streams:
            logger.info("WebSocket connection established, creating MCP client session...")
            async with mcp.ClientSession(*streams) as session:
                # List available tools
                logger.info("Listing available tools...")
                tools_result = await session.list_tools()
                
                # Handle the ListToolsResult format from the MCP API
                if tools_result:
                    logger.debug(f"Tools result type: {type(tools_result)}")
                    logger.debug(f"Tools result: {tools_result}")
                    
                    # Extract tools from the ListToolsResult
                    available_tools = []
                    
                    # Check if it has a 'tools' attribute (most likely case based on the debug output)
                    if hasattr(tools_result, 'tools') and tools_result.tools:
                        for tool in tools_result.tools:
                            if hasattr(tool, 'name'):
                                available_tools.append(tool.name)
                            elif isinstance(tool, dict) and 'name' in tool:
                                available_tools.append(tool['name'])
                    # Fall back to other formats if needed
                    elif isinstance(tools_result, list):
                        for tool in tools_result:
                            if hasattr(tool, 'name'):
                                available_tools.append(tool.name)
                            elif isinstance(tool, dict) and 'name' in tool:
                                available_tools.append(tool['name'])
                    elif isinstance(tools_result, tuple):
                        # If it's a tuple, try to convert to strings
                        available_tools = [str(t) for t in tools_result]
                    
                    # Display the results
                    if available_tools:
                        logger.info(f"Available tools: {', '.join(available_tools)}")
                    else:
                        logger.warning("Could not extract tool names from result")
                        logger.warning(f"Raw tools result: {tools_result}")
                        logger.info("Available tools: (none extracted)")
                else:
                    logger.info("No tools available")
                    available_tools = []
                
                # Check if we're making a tool call or sending a message
                if tool_call:
                    # Call a specific tool
                    tool_name = tool_call.get("name")
                    tool_params = tool_call.get("parameters", {})
                    
                    logger.info(f"Calling tool: {tool_name} with parameters: {tool_params}")
                    
                    # Call the tool with parameters
                    try:
                        tool_result = await session.call_tool(tool_name, tool_params)
                        
                        logger.info(f"Tool result received (type: {type(tool_result)})")
                        logger.debug(f"Tool result: {tool_result}")
                        
                        # Format the result as text
                        if isinstance(tool_result, (dict, list)):
                            result_text = json.dumps(tool_result, indent=2)
                        else:
                            result_text = str(tool_result)
                            
                        return {
                            "status": "success",
                            "agent_id": agent_id,
                            "tool_name": tool_name,
                            "tool_result": tool_result,
                            "response": f"Tool {tool_name} result:\n{result_text}"
                        }
                    except Exception as e:
                        logger.error(f"Error calling tool {tool_name}: {e}")
                        logger.error(traceback.format_exc())
                        return {
                            "status": "error",
                            "agent_id": agent_id,
                            "tool_name": tool_name,
                            "error": f"Error calling tool: {e}"
                        }
                else:
                    # Send a regular message
                    logger.info(f"Sending prompt to agent: {prompt[:50]}...")
                    
                    # Create an MCP message with the prompt
                    logger.info("Creating MCP message...")
                    message = mcp.Message(
                        role="user",
                        content={"content_type": "text", "parts": [{"type": "text", "text": prompt}]}
                    )
                    
                    # Send the message and get a response
                    logger.info("Sending message to agent...")
                    response = await session.send_message(message)
                    
                    # Extract text from the response
                    response_text = ""
                    logger.info("Processing response...")
                    for part in response.content.parts:
                        if part.type == "text":
                            response_text += part.text
                    
                    logger.info(f"Successfully received response from agent (length: {len(response_text)})")
                    
                    return {
                        "status": "success",
                        "agent_id": agent_id,
                        "response": response_text,
                        "raw_response": response.dict()
                    }
    except Exception as e:
        logger.error(f"Error calling Smithery agent {agent_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise ValueError(f"Failed to call Smithery agent: {e}")