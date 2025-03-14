from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import networkx as nx
import asyncio
import json
import matplotlib.pyplot as plt
from io import BytesIO

app = FastAPI()

# Enable CORS (for frontend integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simulated health check function
async def check_health(component: str) -> str:
    await asyncio.sleep(1)  # Simulating async check
    return "Healthy" if hash(component) % 3 != 0 else "Failed"

# Convert JSON into a DAG
def parse_json_to_dag(json_data):
    graph = nx.DiGraph()
    for node, dependencies in json_data.items():
        graph.add_node(node)
        for dep in dependencies:
            graph.add_edge(dep, node)
    return graph

# Traverse DAG using BFS and check health asynchronously
async def traverse_and_check_health(graph):
    health_status = {}
    queue = list(nx.topological_sort(graph))  # BFS Order
    tasks = {node: asyncio.create_task(check_health(node)) for node in queue}

    for node in queue:
        health_status[node] = await tasks[node]

    return health_status

# Generate HTML table for system health
def generate_table_html(health_status):
    table_html = "<table border='1' style='width:50%; border-collapse: collapse;'>"
    table_html += "<tr><th>Component</th><th>Health</th></tr>"
    for component, status in health_status.items():
        color = "red" if status == "Failed" else "green"
        table_html += f"<tr><td>{component}</td><td style='color:{color};'>{status}</td></tr>"
    table_html += "</table>"
    return table_html

# Generate a graph visualization
def visualize_graph(graph, health_status):
    plt.figure(figsize=(12, 10))
    pos = nx.spring_layout(graph)
    colors = ["red" if health_status[node] == "Failed" else "green" for node in graph.nodes]

    nx.draw(graph, pos, with_labels=True, node_color=colors, edge_color="black", node_size=2000, font_size=10)
    
    img = BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    return img

# API Endpoint: System Health Check (Returns HTML Table)
@app.post("/healthcheck/", response_class=HTMLResponse)
async def healthcheck(file: UploadFile = File(...)):
    try:
        json_data = json.loads(await file.read())
        graph = parse_json_to_dag(json_data)
        health_status = await traverse_and_check_health(graph)
        return generate_table_html(health_status)
    except Exception as e:
        return f"<h3>Error: {str(e)}</h3>"

# API Endpoint: Graph Visualization (Returns PNG Image)
@app.post("/visualize/")
async def visualize(file: UploadFile = File(...)):
    try:
        json_data = json.loads(await file.read())
        graph = parse_json_to_dag(json_data)
        health_status = await traverse_and_check_health(graph)
        img = visualize_graph(graph, health_status)
        return StreamingResponse(img, media_type="image/png")
    except Exception as e:
        return {"error": str(e)}

# Run the API locally (for testing)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
