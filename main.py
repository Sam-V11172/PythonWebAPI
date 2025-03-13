from fastapi import FastAPI, UploadFile, File
import networkx as nx
import asyncio
import aiohttp
import json
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import uvicorn

app = FastAPI()

async def check_health(component: str) -> str:
    await asyncio.sleep(1)
    return "Healthy" if hash(component) % 3 != 0 else "Failed"

def parse_json_to_dag(json_data):
    graph = nx.DiGraph()
    for node, dependencies in json_data.items():
        graph.add_node(node)
        for dep in dependencies:
            graph.add_edge(dep, node)
    return graph

async def traverse_and_check_health(graph):
    health_status = {}
    tasks = {node: asyncio.create_task(check_health(node)) for node in nx.topological_sort(graph)}
    for node in tasks:
        health_status[node] = await tasks[node]
    return health_status

def generate_table(health_status):
    df = pd.DataFrame(health_status.items(), columns=["Component", "Health"])
    return df.to_string(index=False)

def visualize_graph(graph, health_status):
    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(graph)
    colors = ["red" if health_status[node] == "Failed" else "green" for node in graph.nodes]
    nx.draw(graph, pos, with_labels=True, node_color=colors, edge_color="black", node_size=2000, font_size=10)
    img = BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    return img

@app.post("/healthcheck/")
async def healthcheck(file: UploadFile = File(...)):
    try:
        json_data = json.loads(await file.read())
        graph = parse_json_to_dag(json_data)
        health_status = await traverse_and_check_health(graph)
        table_result = generate_table(health_status)
        img = visualize_graph(graph, health_status)
        return {"table": table_result, "graph_image": img.getvalue().hex()}
    except Exception as e:
        return {"error": str(e)}

uvicorn.run(app, host="0.0.0.0", port=8000)
