from fastapi import APIRouter, BackgroundTasks
from .models import Event
from . import dedup
import time
import asyncio
from typing import List, Union

router = APIRouter()

# In-memory queue untuk simulasi consumer
event_queue = asyncio.Queue()

stats = {
    "received": 0,
    "unique_processed": 0,
    "duplicate_dropped": 0,
    "topics": set(),
    "start_time": time.time()
}

async def event_consumer():
    """Background task untuk memproses event dari queue."""
    while True:
        event = await event_queue.get()
        try:
            stats["topics"].add(event.topic)
            if dedup.is_duplicate(event):
                stats["duplicate_dropped"] += 1
            else:
                stats["unique_processed"] += 1
        except Exception as e:
            # Jika ada error database/skema, log tapi jangan hentikan loop
            import logging
            logging.error(f"Error processing event: {e}")
        finally:
            event_queue.task_done()

@router.on_event("startup")
async def startup_event():
    dedup.init_db()
    # Jalankan consumer di background
    asyncio.create_task(event_consumer())

@router.post("/publish")
async def publish_event(event: Union[Event, List[Event]]):
    # Cek apakah input adalah single atau list
    events = [event] if isinstance(event, Event) else event
    
    for e in events:
        stats["received"] += 1
        # Masukkan ke queue (non-blocking)
        await event_queue.put(e)
    
    return {
        "status": "accepted", 
        "message": f"{len(events)} event(s) queued for processing"
    }

@router.get("/stats")
async def get_stats():
    return {
        "received": stats["received"],
        "unique_processed": stats["unique_processed"],
        "duplicate_dropped": stats["duplicate_dropped"],
        "topics": list(stats["topics"]),
        "uptime": time.time() - stats["start_time"],
        "queue_size": event_queue.qsize()
    }

@router.get("/events")
async def get_events(topic: str):
    # Ambil data dari SQLite
    events = dedup.get_events_by_topic(topic)
    return {
        "topic": topic, 
        "count": len(events),
        "events": events
    }