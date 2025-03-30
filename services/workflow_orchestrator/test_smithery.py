#!/usr/bin/env python3
"""
Test script for Smithery.ai integration
This script demonstrates how to connect to a Smithery.ai agent using the MCP protocol
"""

import os
import asyncio
import argparse
import smithery
import mcp
from mcp.client.websocket import websocket_client
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("smithery_test")

# Load environment variables
load_dotenv()

async def test_smithery_connection(agent_id, prompt, api_key=None, params=None):
    """
    Test connection to a Smithery.ai agent
    
    Args:
        agent_id (str): Smithery agent ID (e.g. "@turkyden/weather")
        prompt (str): Prompt to send to the agent
        api_key (str, optional): Smithery API key. If not provided, will use SMITHERY_API_KEY env var.
        params (dict, optional): Additional parameters to pass to the agent
    """
    # Use provided API key or get from environment
    api_key = api_key or os.getenv("SMITHERY_API_KEY", "")
    
    if not api_key:
        logger.error("No API key provided and SMITHERY_API_KEY not set in environment")
        return
    
    # Normalize agent_id
    if not agent_id.startswith("@"):
        agent_id = f"@{agent_id}"
    
    # If agent_id doesn't contain a slash, assume it's a user and add a placeholder agent name
    if "/" not in agent_id:
        logger.warning(f"Agent ID {agent_id} doesn't contain a slash. Adding placeholder agent name.")
        agent_id = f"{agent_id}/agent"
    
    logger.info(f"Testing connection to Smithery agent: {agent_id}")
    
    # Create URL for the WebSocket connection
    agent_path = agent_id.lstrip("@")
    url = smithery.create_smithery_url(f"wss://server.smithery.ai/{agent_path}/ws", params or {})
    url = f"{url}&api_key={api_key}"
    
    logger.info("Connecting to Smithery server...")
    
    try:
        # Connect to the server using websocket client
        async with websocket_client(url) as streams:
            async with mcp.ClientSession(*streams) as session:
                # List available tools
                tools_result = await session.list_tools()
                tool_names = [t.name for t in tools_result]
                logger.info(f"Available tools: {', '.join(tool_names)}")
                
                # Send a message to the agent
                logger.info(f"Sending prompt: {prompt}")
                
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
                
                logger.info(f"Response from agent: {response_text}")
                return {
                    "status": "success",
                    "agent_id": agent_id,
                    "available_tools": tool_names,
                    "response": response_text
                }
                
    except Exception as e:
        logger.error(f"Error connecting to Smithery agent: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Smithery.ai integration")
    parser.add_argument("agent_id", help="Smithery agent ID (e.g. @turkyden/weather)")
    parser.add_argument("prompt", help="Prompt to send to the agent")
    parser.add_argument("--api-key", help="Smithery API key (if not set in environment)")
    args = parser.parse_args()
    
    # Run the test
    asyncio.run(test_smithery_connection(args.agent_id, args.prompt, args.api_key))