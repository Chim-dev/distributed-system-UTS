import uvicorn
from fastapi import FastAPI
from .api import router  # Import objek router dari api.py

app = FastAPI(title="Log Aggregator Service")

# Include router-nya
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8080, reload=True)