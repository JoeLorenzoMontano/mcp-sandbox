# MCP Agent Framework

A Docker-based framework for designing and implementing AI agent workflows using the Multimodal Chat Protocol (MCP) with local Ollama models and Smithery.ai integration.

## System Architecture

This system consists of three main components:

1. **MCP Server**: A service that implements the MCP protocol and communicates with Ollama for model responses
2. **Workflow Orchestrator**: Manages multi-step workflows by connecting different MCP servers and Smithery.ai agents
3. **MCP Client**: A web interface to create and execute agent workflows

## Prerequisites

- Docker and Docker Compose
- Ollama installed locally (running on port 11434)
- Desired models pulled in Ollama (e.g., `ollama pull llama3:latest`)

## Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Modify the following settings as needed:

- `OLLAMA_BASE_URL`: URL to your Ollama instance (default: http://host.docker.internal:11434)
- `OLLAMA_MODEL`: Default model to use (default: llama3:latest)
- `SMITHERY_API_KEY`: API key for Smithery.ai integration
- `SMITHERY_REGISTRY_URL`: URL for the Smithery.ai registry (default: https://registry.smithery.ai)
- `EXTERNAL_MCP_SERVERS`: Optional comma-separated list of external MCP servers

## Getting Started

1. Start the services:

```bash
docker-compose up -d
```

2. Access the web interface:

Open your browser and navigate to http://localhost:8002

3. Create a workflow:
   - Enter an input prompt
   - Define one or more workflow steps
   - Run the workflow

## Service Endpoints

- MCP Server: http://localhost:8000
  - `/v1/chat` - MCP compatible chat endpoint

- Workflow Orchestrator: http://localhost:8001
  - `/v1/workflow` - Workflow execution endpoint
  - `/v1/mcp-servers` - List available MCP servers
  - `/v1/test-smithery` - Test connection to a Smithery.ai agent

- MCP Client: http://localhost:8002
  - Web interface for creating and running workflows

## Examples

### Simple Research Workflow

1. Create a two-step workflow:
   - Step 1: "Research" - Generate information about a topic
   - Step 2: "Summarize" - Take the research and create a concise summary

2. Enter a prompt like "Tell me about the history of artificial intelligence"

3. Run the workflow to get both detailed research and a summary

## Extending

### Adding External MCP Servers

Edit the `.env` file and add external MCP servers to the `EXTERNAL_MCP_SERVERS` variable as a comma-separated list.

### Using Smithery.ai Agents

1. Get an API key from Smithery.ai
2. Add your API key to the `.env` file
3. In the web interface, you'll see additional fields for Smithery-specific configuration:
   - Smithery Agent ID: The ID of the specific agent you want to use (e.g., "@turkyden/weather")
   - Smithery Parameters: JSON object with additional parameters for the agent

The system integrates with Smithery.ai agents using the WebSocket MCP protocol, allowing for real-time interaction with specialized agents.

### Weather Agent Example

A complete example of integrating with the Smithery.ai weather agent is included:

```bash
# Run the example script to test weather information
cd services/workflow_orchestrator
./weather_example.py "San Francisco"

# Run the full workflow example
cd examples
./run_weather_workflow.py "New York"
```

See the `services/workflow_orchestrator/README.md` file for detailed information on the Smithery.ai integration.

### Creating Custom Workflows

You can define and save workflow templates by modifying the client interface or creating API scripts that use the workflow orchestrator endpoint.

### Adding Tools and Capabilities

Modify the `tools` parameter in the MCP requests to add specific capabilities to your agents.