from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
import networkx as nx
import asyncio
import json
import matplotlib.pyplot as plt
import uvicorn
from io import BytesIO

# ===========================
# Architecture Decision Record: Why DFS vs BFS
# ===========================
# **Decision**: I used Depth First Search (DFS) for traversing the Directed Acyclic Graph (DAG).
# **Rationale**: DFS fits the problem where we need to check dependencies first before checking the current component's health. 
#    This avoids checking components in parallel that depend on each other.

# ===========================
# Architecture Decision Record: Why Uvicorn vs Gunicorn + Uvicorn
# ===========================
# **Decision**: I used Uvicorn is used as the ASGI server.
# **Rationale**: Uvicorn is lightweight and optimized for asynchronous applications, and FastAPI works natively with Uvicorn, 
#    making it a simpler and more efficient choice compared to using Gunicorn with Uvicorn.

# ===========================
# Architecture Decision Record: FastAPI vs Django
# ===========================
# **Decision**: I used FastAPI as the web framework.
# **Rationale**: FastAPI provides high performance, built-in asynchronous support, and automatic data validation, making it ideal for APIs with I/O-bound operations.

# ===========================
# Architecture Decision Record: Asynchronous Programming
# ===========================
# **Decision**: I used Asynchronous Programming in health check functions
# **Rationale**: Asynchronous execution allows handling multiple health checks concurrently, improving performance and scalability by avoiding blocking I/O operations.

# ===========================
# Architecture Decision Record: NetworkX for DAG Representation
# ===========================
# **Decision**: I used NetworkX to represent and manipulate the Directed Acyclic Graph (DAG).
# **Rationale**: NetworkX is a powerful Python library for creating, analyzing, and visualizing complex networks. 
#    It simplifies working with directed graphs, making it a suitable choice for representing dependencies in the health check system.

# ===========================
# Architecture Decision Record: Use of Matplotlib for Visualization
# ===========================
# **Decision**: I used Matplotlib to generate visual representations of the DAG.
# **Rationale**: Matplotlib is a robust library for generating static visualizations in Python. 
#    It integrates well with NetworkX for graph drawing, making it a good fit for generating a clear, customizable image of the DAG.


# ===========================
# Architecture Decision Record: JSON for Data Representation
# ===========================
# **Decision**: I used JSON is used to represent the input data for the DAG structure.
# **Rationale**: JSON is a lightweight, human-readable, and widely used format for data interchange, 
#    making it a convenient choice for exchanging data between the client and the server.


app = FastAPI()

# Simulated health check function
async def perform_health_check(component: str) -> str:
    await asyncio.sleep(1)  # Simulating async health check
    return "Healthy" if hash(component) % 3 != 0 else "Failed"

# Convert incoming JSON data into a Directed Acyclic Graph (DAG)
def create_dag_from_json(data):
    dag = nx.DiGraph()  # Initialize a directed graph
    for component, dependencies in data.items():
        dag.add_node(component)  # Add the node (component)
        for dep in dependencies:
            dag.add_edge(dep, component)  # Add edges (dependencies) from parent to component
    return dag

# Depth First Search (DFS) to traverse the DAG and check health asynchronously
async def dfs_check_and_evaluate(dag, component, status_map):
    """ Recursively perform DFS traversal and evaluate health for each component. """
    if component not in status_map:  # If the component hasn't been checked yet
        for dependency in dag.neighbors(component):  # Traverse the dependencies (parents)
            await dfs_check_and_evaluate(dag, dependency, status_map)
        status_map[component] = await perform_health_check(component)  # Now check the health of the current component

# Generate a simple text-based table for health status results
def generate_status_table(status_map):
    table = "Component     | Health\n"
    table += "-" * 30 + "\n"
    for component, status in status_map.items():
        table += f"{component:<15} | {status}\n"
    return table

# Generate a visual representation of the DAG with health statuses
def generate_dag_image(dag, status_map, random_seed=42):
    plt.figure(figsize=(12, 10))
    
    # Use spring_layout with a fixed seed for a consistent layout across runs
    layout = nx.spring_layout(dag, seed=random_seed)  # Position the nodes
    
    # Color the nodes based on their health status (Green: Healthy, Red: Failed)
    node_colors = ["red" if status_map[node] == "Failed" else "green" for node in dag.nodes]
    
    # Draw the graph
    nx.draw(dag, layout, with_labels=True, node_color=node_colors, edge_color="black", node_size=2000, font_size=10)
    
    # Save the plot to a BytesIO stream and return
    img_stream = BytesIO()
    plt.savefig(img_stream, format="png")
    img_stream.seek(0)
    return img_stream

# Endpoint for Health Check (Returns a Plain Text Table)
@app.post("/healthcheck/") 
async def health_check(file: UploadFile = File(...)):
    try:
        data = json.loads(await file.read())  # Parse the uploaded JSON file
        dag = create_dag_from_json(data)  # Create a DAG from the JSON data
        status_map = {}  # Dictionary to hold the health status of each component
        
        # Perform DFS to check health of all components
        for component in dag.nodes:
            if component not in status_map:  # Only check unvisited components
                await dfs_check_and_evaluate(dag, component, status_map)
        
        status_table = generate_status_table(status_map)  # Generate the status table
        return status_table  # Return the plain text health status table
        
    except Exception as e:
        return f"Error: {str(e)}"

# Endpoint for Graph Visualization (Returns PNG Image)
@app.post("/graph/") 
async def graph(file: UploadFile = File(...)):
    try:
        data = json.loads(await file.read())  # Parse the uploaded JSON file
        dag = create_dag_from_json(data)  # Create a DAG from the JSON data
        status_map = {}  # Dictionary to hold the health status of each component
        
        # Perform DFS to check health of all components
        for component in dag.nodes:
            if component not in status_map:  # Only check unvisited components
                await dfs_check_and_evaluate(dag, component, status_map)
        
        img_stream = generate_dag_image(dag, status_map)  # Generate the DAG image with health status
        return StreamingResponse(img_stream, media_type="image/png")  # Return the image as PNG
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
