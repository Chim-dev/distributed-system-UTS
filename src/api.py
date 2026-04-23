from fastapi import FastAPI
from .models import Event
from . import dedup
import time

# Ubah jadi router biar bisa di-include
router = FastAPI()

stats = {
    "received": 0,
    "unique_processed": 0,
    "duplicate_dropped": 0,
    "topics": set(),
    "start_time": time.time()
}

@router.on_event("startup")
async def startup_event():
    dedup.init_db()

@router.post("/publish")
async def publish_event(event: Event):
    stats["received"] += 1
    stats["topics"].add(event.topic)
    
    if dedup.is_duplicate(event.topic, event.event_id):
        stats["duplicate_dropped"] += 1
        return {"status": "dropped", "message": "Duplicate event"}
    
    stats["unique_processed"] += 1
    return {"status": "processed", "message": "Event accepted"}

@router.get("/stats")
async def get_stats():
    return {
        "received": stats["received"],
        "unique_processed": stats["unique_processed"],
        "duplicate_dropped": stats["duplicate_dropped"],
        "topics": list(stats["topics"]),
        "uptime": time.time() - stats["start_time"]
    }