#!/usr/bin/env python3
"""
Test script for Smithery.ai integration
This script demonstrates how to connect to a Smithery.ai agent using the MCP protocol
"""

import os
import sys
import asyncio
import argparse
import traceback
import smithery
import mcp
from mcp.client.websocket import websocket_client
from dotenv import load_dotenv
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("smithery_test")

# Load environment variables
load_dotenv()

async def test_smithery_connection(agent_id, prompt, api_key=None, params=None, debug=False, tool_call=None):
    """
    Test connection to a Smithery.ai agent
    
    Args:
        agent_id (str): Smithery agent ID (e.g. "@turkyden/weather")
        prompt (str): Prompt to send to the agent
        api_key (str, optional): Smithery API key. If not provided, will use SMITHERY_API_KEY env var.
        params (dict, optional): Additional parameters to pass to the agent
        debug (bool, optional): Enable debug logging
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
    api_key = api_key or os.getenv("SMITHERY_API_KEY", "")
    
    if not api_key:
        logger.error("No API key provided and SMITHERY_API_KEY not set in environment")
        return {
            "status": "error",
            "error": "No API key provided"
        }
    
    logger.info(f"Using Smithery API key: {api_key[:5]}...{api_key[-5:]}")
    
    # Normalize agent_id
    if not agent_id.startswith("@"):
        agent_id = f"@{agent_id}"
    
    # If agent_id doesn't contain a slash, assume it's a user and add a placeholder agent name
    if "/" not in agent_id:
        logger.warning(f"Agent ID {agent_id} doesn't contain a slash. Adding placeholder agent name.")
        agent_id = f"{agent_id}/agent"
    
    logger.info(f"Testing connection to Smithery agent: {agent_id}")
    
    try:
        # Create URL for the WebSocket connection
        logger.info(f"Creating Smithery URL for agent: {agent_id}")
        agent_path = agent_id.lstrip("@")
        url = smithery.create_smithery_url(f"wss://server.smithery.ai/{agent_path}/ws", params or {})
        url = f"{url}&api_key={api_key}"
        logger.debug(f"URL (without API key): {url.split('&api_key=')[0]}")
    except Exception as e:
        logger.error(f"Error creating Smithery URL: {e}")
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "error": f"Error creating Smithery URL: {e}"
        }
    
    logger.info("Connecting to Smithery server...")
    
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
                    tool_names = []
                    
                    # Check if it has a 'tools' attribute (most likely case based on the debug output)
                    if hasattr(tools_result, 'tools') and tools_result.tools:
                        for tool in tools_result.tools:
                            if hasattr(tool, 'name'):
                                tool_names.append(tool.name)
                            elif isinstance(tool, dict) and 'name' in tool:
                                tool_names.append(tool['name'])
                    # Fall back to other formats if needed
                    elif isinstance(tools_result, list):
                        for tool in tools_result:
                            if hasattr(tool, 'name'):
                                tool_names.append(tool.name)
                            elif isinstance(tool, dict) and 'name' in tool:
                                tool_names.append(tool['name'])
                    elif isinstance(tools_result, tuple):
                        # If it's a tuple, try to convert to strings
                        tool_names = [str(t) for t in tools_result]
                    
                    # Display the results
                    if tool_names:
                        logger.info(f"Available tools: {', '.join(tool_names)}")
                    else:
                        logger.warning("Could not extract tool names from result")
                        logger.warning(f"Raw tools result: {tools_result}")
                        logger.info("Available tools: (none extracted)")
                else:
                    logger.info("No tools available")
                    tool_names = []
                
                # Check if we're calling a tool or sending a message
                if tool_call:
                    # Call a specific tool
                    tool_name = tool_call.get("name")
                    tool_params = tool_call.get("parameters", {})
                    
                    logger.info(f"Calling tool: {tool_name} with parameters: {tool_params}")
                    
                    try:
                        # Call the tool directly using the simplified format
                        tool_result = await session.call_tool(tool_name, tool_params)
                        
                        logger.info(f"Tool result type: {type(tool_result)}")
                        logger.debug(f"Tool result: {tool_result}")
                        
                        # Format the result into a string
                        if isinstance(tool_result, (dict, list)):
                            response_text = json.dumps(tool_result, indent=2, default=str)
                        else:
                            response_text = str(tool_result)
                        
                        logger.info(f"Tool {tool_name} call successful")
                        print(f"\nTool {tool_name} result:")
                        print(response_text)
                    except Exception as e:
                        logger.error(f"Error calling tool {tool_name}: {e}")
                        logger.error(traceback.format_exc())
                        
                        # Fall back to sending a message
                        logger.info(f"Falling back to sending general prompt: {prompt}")
                        
                        # Create an MCP message with the prompt
                        message = mcp.Message(
                            role="user",
                            content={"content_type": "text", "parts": [{"type": "text", "text": prompt}]}
                        )
                        
                        # Send the message and get a response
                        response = await session.send_message(message)
                        
                        # Extract text from the response
                        response_text = ""
                        logger.info("Processing response...")
                        for part in response.content.parts:
                            if part.type == "text":
                                response_text += part.text
                else:
                    # Send a regular message
                    logger.info(f"Sending prompt: {prompt}")
                    
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
                
                logger.info(f"Response from agent: {response_text}")
                
                # Prepare the result based on whether we called a tool or sent a message
                if tool_call and 'tool_result' in locals():
                    result = {
                        "status": "success",
                        "agent_id": agent_id,
                        "available_tools": tool_names,
                        "tool_name": tool_call.get("name"),
                        "tool_result": tool_result,
                        "response": response_text
                    }
                else:
                    result = {
                        "status": "success",
                        "agent_id": agent_id,
                        "available_tools": tool_names,
                        "response": response_text
                    }
                
                print("\nResponse from Smithery agent:")
                print("=" * 50)
                print(response_text)
                print("=" * 50)
                
                return result
                
    except Exception as e:
        logger.error(f"Error connecting to Smithery agent: {e}")
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Smithery.ai integration")
    parser.add_argument("agent_id", help="Smithery agent ID (e.g. @turkyden/weather)")
    parser.add_argument("prompt", help="Prompt to send to the agent")
    parser.add_argument("--api-key", help="Smithery API key (if not set in environment)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--output", help="Save response to file")
    parser.add_argument("--tool", help="Tool name to call instead of sending a message")
    parser.add_argument("--params", help="JSON string of parameters for the tool call")
    args = parser.parse_args()
    
    try:
        # Prepare tool call if specified
        tool_call = None
        if args.tool:
            tool_params = {}
            if args.params:
                try:
                    tool_params = json.loads(args.params)
                except json.JSONDecodeError:
                    print(f"Error: Invalid JSON parameters: {args.params}")
                    sys.exit(1)
            
            tool_call = {
                "name": args.tool,
                "parameters": tool_params
            }
            print(f"Calling tool: {args.tool} with parameters: {tool_params}")
        
        # Run the test
        result = asyncio.run(test_smithery_connection(
            args.agent_id, 
            args.prompt, 
            args.api_key,
            debug=args.debug,
            tool_call=tool_call
        ))
        
        # Save result to file if specified
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
                print(f"Results saved to {args.output}")
        
        # Exit with error code if failed
        if result["status"] == "error":
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)