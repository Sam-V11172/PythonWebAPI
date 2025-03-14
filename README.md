-------Run in terminal to start the api:
uvicorn main:app --reload

-------HealthCheck
curl -X POST 'http://127.0.0.1:8000/healthcheck/' -F 'file=@/Users/sandilyadongar/sample.json'

-------Graph
curl -X POST 'http://127.0.0.1:8000/graph/' -F 'file=@/Users/sandilyadongar/sample.json' --output graph.png
