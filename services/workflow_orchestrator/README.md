# Workflow Orchestrator with Smithery.ai Integration

This service orchestrates workflows between different MCP servers, including integration with Smithery.ai agents via the WebSocket MCP protocol.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
# Create a .env file in the workflow_orchestrator directory
echo "SMITHERY_API_KEY=your-api-key-here" > .env
```

## Smithery.ai Integration

The workflow orchestrator now supports direct integration with Smithery.ai agents using WebSockets. This allows you to incorporate Smithery.ai agents into your workflows.

### Test Scripts

1. **Basic Smithery Test**: Test connectivity to any Smithery.ai agent
```bash
# Usage
./test_smithery.py "@agent_owner/agent_name" "Your prompt here"

# Example - Test the weather agent
./test_smithery.py "@turkyden/weather" "What's the weather in New York?"
```

2. **Weather Example**: Specifically for testing the weather agent
```bash
# Usage
./weather_example.py "Location"

# Example
./weather_example.py "San Francisco"
```

### Using Smithery.ai in Workflows

When defining a workflow step, you can specify a Smithery.ai agent to use:

```python
# Example workflow step using a Smithery agent
{
  "name": "Weather Check",
  "role": "user",
  "smithery_agent_id": "@turkyden/weather",
  "smithery_params": {"temperature": 0.7}  # Optional parameters
}
```

### API Endpoints

1. **Run Workflow**: Run a workflow that can include Smithery.ai agents
```
POST /v1/workflow
```

2. **Test Smithery Connection**: Test connection to a specific Smithery.ai agent
```
POST /v1/test-smithery
{
  "agent_id": "@turkyden/weather",
  "prompt": "What's the weather in Paris?",
  "params": {}  # Optional
}
```

3. **List Available MCP Servers**: List all available MCP servers, including Smithery.ai servers
```
GET /v1/mcp-servers
```

## Troubleshooting

If you encounter connection issues:

1. Verify your Smithery API key is correct
2. Check that the agent ID is formatted correctly (e.g., `@username/agent`)
3. Ensure the Smithery.ai service is available
4. Check the logs for detailed error messages