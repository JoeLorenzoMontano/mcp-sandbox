#!/usr/bin/env python3
"""
Example script to run a weather workflow using the workflow orchestrator API
"""

import os
import json
import httpx
import argparse
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8001")

async def run_workflow(location):
    """Run a weather workflow for the given location"""
    
    # Load the workflow template
    with open(os.path.join(os.path.dirname(__file__), "weather_workflow.json"), "r") as f:
        workflow = json.load(f)
    
    # Update the input with the provided location
    workflow["input"] = f"What's the weather like in {location}?"
    
    print(f"Running weather workflow for {location}...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{ORCHESTRATOR_URL}/v1/workflow",
                json=workflow,
                timeout=60.0
            )
            
            if response.status_code != 200:
                print(f"Error: {response.status_code} - {response.text}")
                return
            
            result = response.json()
            
            # Print the workflow results
            print("\n===== WORKFLOW RESULTS =====\n")
            
            for i, step_result in enumerate(result["results"]):
                print(f"Step {i+1}: {step_result['step_name']}")
                print(f"MCP Server: {step_result['mcp_server']}")
                print("\nResponse:")
                
                # Extract the text response
                message = step_result["response"].get("message", {})
                content = message.get("content", {})
                parts = content.get("parts", [])
                
                text_response = ""
                for part in parts:
                    if part.get("type") == "text":
                        text_response += part.get("text", "")
                
                print(f"{text_response}\n")
                print("-" * 50)
            
        except Exception as e:
            print(f"Error running workflow: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a weather workflow")
    parser.add_argument("location", help="Location to get weather for")
    args = parser.parse_args()
    
    asyncio.run(run_workflow(args.location))