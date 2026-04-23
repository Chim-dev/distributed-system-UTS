import uvicorn
from fastapi import FastAPI
from .api import app as api_router

# Kita gabungin app dari api.py
app = FastAPI(title="Log Aggregator Service")

# Mount atau include router dari api.py
app.include_router(api_router.router)

if __name__ == "__main__":
    # Jalanin server di port 8080 sesuai requirement
    uvicorn.run("src.main:app", host="0.0.0.0", port=8080, reload=True)