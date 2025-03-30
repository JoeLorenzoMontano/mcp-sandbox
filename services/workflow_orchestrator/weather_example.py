#!/usr/bin/env python3
"""
Example script for using the Smithery.ai weather agent
This script demonstrates how to connect to the @turkyden/weather agent using the MCP protocol
"""

import os
import asyncio
import smithery
import mcp
from mcp.client.websocket import websocket_client
from dotenv import load_dotenv
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("weather_example")

# Load environment variables
load_dotenv()

async def get_weather(location, api_key=None):
    """
    Get weather information for a location using the Smithery.ai weather agent
    
    Args:
        location (str): The location to get weather for
        api_key (str, optional): Smithery API key. If not provided, will use SMITHERY_API_KEY env var.
    """
    # Use provided API key or get from environment
    api_key = api_key or os.getenv("SMITHERY_API_KEY", "")
    
    if not api_key:
        logger.error("No API key provided and SMITHERY_API_KEY not set in environment")
        return
    
    # Create Smithery URL with server endpoint
    url = smithery.create_smithery_url("wss://server.smithery.ai/@turkyden/weather/ws", {})
    url = f"{url}&api_key={api_key}"
    
    logger.info(f"Connecting to weather agent for location: {location}")
    
    try:
        # Connect to the server using websocket client
        async with websocket_client(url) as streams:
            async with mcp.ClientSession(*streams) as session:
                # List available tools
                tools_result = await session.list_tools()
                tool_names = [t.name for t in tools_result]
                logger.info(f"Available tools: {', '.join(tool_names)}")
                
                # Create a prompt for the weather
                prompt = f"What's the weather like in {location}?"
                
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
                logger.info(f"Sending prompt to weather agent: {prompt}")
                response = await session.send_message(message)
                
                # Extract text from the response
                response_text = ""
                for part in response.content.parts:
                    if part.type == "text":
                        response_text += part.text
                
                logger.info(f"Weather response: {response_text}")
                return response_text
                
    except Exception as e:
        logger.error(f"Error getting weather: {e}")
        return f"Error getting weather: {e}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get weather from Smithery.ai weather agent")
    parser.add_argument("location", help="Location to get weather for")
    parser.add_argument("--api-key", help="Smithery API key (if not set in environment)")
    args = parser.parse_args()
    
    # Run the weather query
    asyncio.run(get_weather(args.location, args.api_key))