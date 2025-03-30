import os
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import json
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_client")

# Orchestrator URL
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://workflow_orchestrator:8001")

app = FastAPI(title="MCP Client")

# Create templates directory
os.makedirs(os.path.join(os.path.dirname(__file__), "templates"), exist_ok=True)

# Create static directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Create the index.html template
index_html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
with open(index_html_path, "w") as f:
    f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Client</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #333;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        textarea, select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
            font-family: inherit;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        .response {
            margin-top: 20px;
            padding: 15px;
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 4px;
            white-space: pre-wrap;
        }
        .workflow-step {
            margin-bottom: 20px;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        .add-step {
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <h1>MCP Workflow Client</h1>
    
    <form id="workflowForm" action="/run-workflow" method="post">
        <div class="form-group">
            <label for="input">Input Prompt:</label>
            <textarea id="input" name="input" rows="5" required></textarea>
        </div>
        
        <div id="workflowSteps">
            <div class="workflow-step" id="step-0">
                <h3>Step 1</h3>
                <div class="form-group">
                    <label for="step-0-name">Step Name:</label>
                    <input type="text" id="step-0-name" name="steps[0][name]" required>
                </div>
                
                <div class="form-group">
                    <label for="step-0-role">Role:</label>
                    <select id="step-0-role" name="steps[0][role]">
                        <option value="user">User</option>
                        <option value="system">System</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="step-0-server">MCP Server (leave blank for default):</label>
                    <input type="text" id="step-0-server" name="steps[0][mcp_server]">
                </div>
                
                <div class="smithery-section">
                    <h4>Smithery.ai Options</h4>
                    <div class="form-group">
                        <label for="step-0-smithery-id">Smithery Agent ID (optional):</label>
                        <input type="text" id="step-0-smithery-id" name="steps[0][smithery_agent_id]">
                    </div>
                    <div class="form-group">
                        <label for="step-0-smithery-params">Smithery Parameters (JSON, optional):</label>
                        <textarea id="step-0-smithery-params" name="steps[0][smithery_params]" rows="3" placeholder='{"temperature": 0.7}'></textarea>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="add-step">
            <button type="button" id="addStep">Add Another Step</button>
        </div>
        
        <button type="submit">Run Workflow</button>
    </form>
    
    <div id="response" class="response" style="display: none;"></div>
    
    <script>
        let stepCount = 1;
        
        document.getElementById('addStep').addEventListener('click', function() {
            const workflowSteps = document.getElementById('workflowSteps');
            const newStep = document.createElement('div');
            newStep.className = 'workflow-step';
            newStep.id = `step-${stepCount}`;
            
            newStep.innerHTML = `
                <h3>Step ${stepCount + 1}</h3>
                <div class="form-group">
                    <label for="step-${stepCount}-name">Step Name:</label>
                    <input type="text" id="step-${stepCount}-name" name="steps[${stepCount}][name]" required>
                </div>
                
                <div class="form-group">
                    <label for="step-${stepCount}-role">Role:</label>
                    <select id="step-${stepCount}-role" name="steps[${stepCount}][role]">
                        <option value="user">User</option>
                        <option value="system">System</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="step-${stepCount}-server">MCP Server (leave blank for default):</label>
                    <input type="text" id="step-${stepCount}-server" name="steps[${stepCount}][mcp_server]">
                </div>
                
                <div class="smithery-section">
                    <h4>Smithery.ai Options</h4>
                    <div class="form-group">
                        <label for="step-${stepCount}-smithery-id">Smithery Agent ID (optional):</label>
                        <input type="text" id="step-${stepCount}-smithery-id" name="steps[${stepCount}][smithery_agent_id]">
                    </div>
                    <div class="form-group">
                        <label for="step-${stepCount}-smithery-params">Smithery Parameters (JSON, optional):</label>
                        <textarea id="step-${stepCount}-smithery-params" name="steps[${stepCount}][smithery_params]" rows="3" placeholder='{"temperature": 0.7}'></textarea>
                    </div>
                </div>
            `;
            
            workflowSteps.appendChild(newStep);
            stepCount++;
        });
        
        document.getElementById('workflowForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const responseDiv = document.getElementById('response');
            responseDiv.style.display = 'block';
            responseDiv.textContent = 'Processing workflow...';
            
            try {
                // Convert form data to the structure needed
                const steps = [];
                const input = formData.get('input');
                
                // Parse step data
                for (let i = 0; i < stepCount; i++) {
                    const smitheryParams = formData.get(`steps[${i}][smithery_params]`);
                    let parsedSmitheryParams = null;
                    
                    // Parse the Smithery params if provided
                    if (smitheryParams && smitheryParams.trim()) {
                        try {
                            parsedSmitheryParams = JSON.parse(smitheryParams);
                        } catch (err) {
                            responseDiv.textContent = `Error: Invalid JSON in Smithery parameters for step ${i+1}`;
                            return;
                        }
                    }
                    
                    steps.push({
                        name: formData.get(`steps[${i}][name]`),
                        role: formData.get(`steps[${i}][role]`),
                        mcp_server: formData.get(`steps[${i}][mcp_server]`) || null,
                        smithery_agent_id: formData.get(`steps[${i}][smithery_agent_id]`) || null,
                        smithery_params: parsedSmitheryParams
                    });
                }
                
                const response = await fetch('/run-workflow', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ steps, input })
                });
                
                const data = await response.json();
                
                // Format and display the response
                let resultHtml = '<h2>Workflow Results</h2>';
                
                data.results.forEach((result, index) => {
                    resultHtml += `
                        <div class="result-step">
                            <h3>Step ${index + 1}: ${result.step_name}</h3>
                            <p><strong>MCP Server:</strong> ${result.mcp_server}</p>
                            <div class="response-content">
                                <pre>${JSON.stringify(result.response, null, 2)}</pre>
                            </div>
                        </div>
                    `;
                });
                
                responseDiv.innerHTML = resultHtml;
                
            } catch (error) {
                responseDiv.textContent = `Error: ${error.message}`;
            }
        });
    </script>
</body>
</html>
""")

# Create API endpoints
@app.get("/smithery-agents")
async def get_smithery_agents():
    try:
        # Get available MCP servers which includes Smithery servers
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ORCHESTRATOR_URL}/v1/mcp-servers")
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Error fetching MCP servers")
            
            # This might need adjustment based on how smithery agents are stored
            server_data = response.json()
            smithery_servers = [
                server for server in server_data.get("servers", [])
                if "smithery.ai" in server 
            ]
            
            if not smithery_servers:
                return {"agents": []}
                
            # Try to fetch agents from the Smithery registry endpoint
            # Note: Adjust this based on the actual Smithery API
            agents = []
            async with httpx.AsyncClient() as registry_client:
                for server in smithery_servers:
                    registry_response = await registry_client.get(
                        f"{server}/agents",
                        headers={"Authorization": f"Bearer {os.getenv('SMITHERY_API_KEY', '')}"},
                        timeout=10.0
                    )
                    
                    if registry_response.status_code == 200:
                        agent_data = registry_response.json()
                        agents.extend(agent_data.get("agents", []))
            
            return {"agents": agents}
                
    except Exception as e:
        logger.error(f"Error fetching Smithery agents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/run-workflow")
async def run_workflow(request: Request):
    data = await request.json()
    
    try:
        logger.info(f"Sending workflow request with {len(data['steps'])} steps")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ORCHESTRATOR_URL}/v1/workflow",
                json=data,
                timeout=120.0  # Longer timeout for workflows
            )
            
            if response.status_code != 200:
                logger.error(f"Orchestrator error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Error from workflow orchestrator")
            
            workflow_result = response.json()
            
        logger.info(f"Workflow completed successfully")
        return workflow_result
        
    except Exception as e:
        logger.error(f"Error running workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/mcp-servers")
async def get_mcp_servers():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ORCHESTRATOR_URL}/v1/mcp-servers")
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Error fetching MCP servers")
            
            return response.json()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)