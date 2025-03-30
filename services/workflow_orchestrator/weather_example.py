#!/usr/bin/env python3
"""
Example script for using the Smithery.ai weather agent
This script demonstrates how to connect to the @turkyden/weather agent using the MCP protocol
"""

import os
import asyncio
import traceback
import smithery
import mcp
from mcp.client.websocket import websocket_client
from dotenv import load_dotenv
import logging
import argparse
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("weather_example")

# Load environment variables
load_dotenv()

async def get_weather(location, api_key=None, debug=False):
    """
    Get weather information for a location using the Smithery.ai weather agent
    
    Args:
        location (str): The location to get weather for
        api_key (str, optional): Smithery API key. If not provided, will use SMITHERY_API_KEY env var.
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
        return "Error: No API key provided"
    
    logger.info(f"Using Smithery API key: {api_key[:5]}...{api_key[-5:]}")
    
    # Create Smithery URL with server endpoint
    try:
        logger.info("Creating Smithery URL...")
        params = {}  # Optional parameters can be added here
        url = smithery.create_smithery_url("wss://server.smithery.ai/@turkyden/weather/ws", params)
        url = f"{url}&api_key={api_key}"
        logger.debug(f"URL (without API key): {url.split('&api_key=')[0]}")
    except Exception as e:
        logger.error(f"Error creating Smithery URL: {e}")
        logger.error(traceback.format_exc())
        return f"Error creating Smithery URL: {e}"
    
    logger.info(f"Connecting to weather agent for location: {location}")
    
    try:
        # Connect to the server using websocket client
        logger.info("Opening WebSocket connection...")
        async with websocket_client(url) as streams:
            logger.info("WebSocket connection established, creating MCP client session...")
            async with mcp.ClientSession(*streams) as session:
                # List available tools
                logger.info("Listing available tools...")
                tools_result = await session.list_tools()
                tool_names = [t.name for t in tools_result]
                logger.info(f"Available tools: {', '.join(tool_names)}")
                
                # Create a prompt for the weather
                prompt = f"What's the weather like in {location}?"
                
                # Create an MCP message with the prompt
                logger.info("Creating MCP message...")
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
                print("\nWeather response:")
                print("=" * 50)
                print(response_text)
                print("=" * 50)
                return response_text
                
    except Exception as e:
        logger.error(f"Error getting weather: {e}")
        logger.error(traceback.format_exc())
        return f"Error getting weather: {e}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get weather from Smithery.ai weather agent")
    parser.add_argument("location", help="Location to get weather for")
    parser.add_argument("--api-key", help="Smithery API key (if not set in environment)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    try:
        # Run the weather query
        result = asyncio.run(get_weather(args.location, args.api_key, args.debug))
        if result and result.startswith("Error:"):
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)