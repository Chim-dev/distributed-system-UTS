import httpx
import asyncio
import uuid
from datetime import datetime
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AGGREGATOR_URL = "http://aggregator:8080/publish"

async def send_batch(client, batch_size=100):
    """Kirim batch event, termasuk duplikat."""
    events = []
    # Buat beberapa ID tetap untuk simulasi duplikat
    fixed_ids = [str(uuid.uuid4()) for _ in range(20)]
    
    for _ in range(batch_size):
        # 20% kemungkinan kirim duplikat
        if random.random() < 0.2:
            event_id = random.choice(fixed_ids)
        else:
            event_id = str(uuid.uuid4())
            
        events.append({
            "topic": "sensor-data",
            "event_id": event_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": "publisher-sim",
            "payload": {"temp": random.uniform(20, 30)}
        })
    
    try:
        resp = await client.post(AGGREGATOR_URL, json=events)
        logger.info(f"Sent {len(events)} events, status: {resp.status_code}")
    except Exception as e:
        logger.error(f"Failed to send: {e}")

async def main():
    logger.info("Starting publisher in 5 seconds...")
    await asyncio.sleep(5) # Tunggu aggregator ready
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Kirim total 5000 event (50 batch x 100)
        for i in range(50):
            await send_batch(client, 100)
            # Sangat cepat, hampir tanpa jeda
            await asyncio.sleep(0.01) 
            
    logger.info("Publisher finished its job.")

if __name__ == "__main__":
    asyncio.run(main())
