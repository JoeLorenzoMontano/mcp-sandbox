# MCP Agent Framework

A Docker-based framework for designing and implementing AI agent workflows using the Multimodal Chat Protocol (MCP) with local Ollama models.

## System Architecture

This system consists of three main components:

1. **MCP Server**: A service that implements the MCP protocol and communicates with Ollama for model responses
2. **Workflow Orchestrator**: Manages multi-step workflows by connecting different MCP servers
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

### Creating Custom Workflows

You can define and save workflow templates by modifying the client interface or creating API scripts that use the workflow orchestrator endpoint.

### Adding Tools and Capabilities

Modify the `tools` parameter in the MCP requests to add specific capabilities to your agents.