from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
import networkx as nx
import aiohttp
import asyncio
import matplotlib.pyplot as plt
import io
import uvicorn
from fastapi.responses import StreamingResponse
from io import BytesIO

# Create a FastAPI web app
app = FastAPI()

# Pydantic model for input graph
class GraphRequest(BaseModel):
    graph: Dict[str, List[str]]


# Function to simulate a health check (replace with actual health check logic)
async def check_health(node: str, session: aiohttp.ClientSession):
    try:
        # Placeholder for making an async HTTP request (to an API, database, etc.)
        # For now, we randomly simulate health check
        health_url = f"https://api.example.com/health/{node}"
        async with session.get(health_url) as response:
            return node, response.status == 200
    except Exception as e:
        return node, False


# Function to perform the BFS traversal and check health of components
async def bfs_health_check(graph: dict):
    results = {}
    visited = set()
    queue = list(graph.keys())  # Start from all components (root nodes)
    
    async with aiohttp.ClientSession() as session:
        while queue:
            node = queue.pop(0)
            if node not in visited:
                visited.add(node)
                health_status = await check_health(node, session)
                results[health_status[0]] = health_status[1]
                
                # Add dependent nodes (downstream components) to the queue
                if node in graph:
                    for neighbor in graph[node]:
                        queue.append(neighbor)

    return results


# Function to visualize the graph with health status
def plot_graph(graph, health_results):
    G = nx.DiGraph(graph)
    node_colors = ['red' if not health_results.get(node, True) else 'green' for node in G.nodes()]
    pos = nx.spring_layout(G)  # Layout for nodes
    nx.draw(G, pos, with_labels=True, node_color=node_colors, font_weight='bold', node_size=3000)
    plt.title("System Health Graph")
    
    # Save the plot to a BytesIO object instead of displaying it
    image_stream = BytesIO()
    plt.savefig(image_stream, format="PNG")
    plt.close()
    image_stream.seek(0)
    return image_stream


# Health check API endpoint
@app.post("/check_health")
async def check_system_health(data: GraphRequest):
    try:
        # Extract graph from the request
        graph = data.graph
        
        # Perform BFS health check
        health_results = await bfs_health_check(graph)
        
        # Visualize the graph with health status
        image_stream = plot_graph(graph, health_results)
        
        # Prepare the health results table in a text-based format
        health_table = "<table border='1'><tr><th>Component</th><th>Status</th></tr>"
        for node, status in health_results.items():
            status_str = "Healthy" if status else "Unhealthy"
            health_table += f"<tr><td>{node}</td><td>{status_str}</td></tr>"
        health_table += "</table>"

        # Return the health results and overall system status
        overall_status = "Healthy" if all(health_results.values()) else "Unhealthy"
        
        return {
            "health_results": health_results,
            "overall_status": overall_status,
            "health_table": health_table,  # Return the HTML table
            "graph_image_url": "/static/graph.png"
        }

# Endpoint to serve the generated graph image
@app.get("/static/graph.png")
async def get_graph_image():
    try:
        # Generate the graph visualization image
        graph_image = plot_graph(sample_graph, {})  # Provide any sample graph
        return StreamingResponse(graph_image, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate graph image")

# Sample graph for testing purposes
sample_graph = {
    "A": ["B", "C"],
    "B": ["D", "E"],
    "C": ["F"],
    "D": [],
    "E": [],
    "F": []
}

# Start the FastAPI server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
