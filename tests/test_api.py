import pytest
import time
import asyncio
from fastapi.testclient import TestClient
from src.main import app
from src.api import event_queue

client = TestClient(app)

def wait_for_queue():
    """Tunggu sebentar agar consumer memproses queue."""
    time.sleep(0.5)

def test_1_publish_single_event():
    payload = {
        "topic": "test",
        "event_id": "unique-1",
        "timestamp": "2026-04-23T16:00:00Z",
        "source": "unit-test",
        "payload": {"data": 1}
    }
    response = client.post("/publish", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"

def test_2_deduplication():
    payload = {
        "topic": "test",
        "event_id": "dup-1",
        "timestamp": "2026-04-23T16:00:00Z",
        "source": "unit-test",
        "payload": {}
    }
    # Kirim pertama
    client.post("/publish", json=payload)
    # Kirim kedua (duplikat)
    client.post("/publish", json=payload)
    
    wait_for_queue()
    
    response = client.get("/stats")
    stats = response.json()
    assert stats["duplicate_dropped"] >= 1

def test_3_batch_publish():
    payloads = [
        {
            "topic": "batch-test",
            "event_id": f"batch-{i}",
            "timestamp": "2026-04-23T16:00:00Z",
            "source": "unit-test",
            "payload": {}
        } for i in range(5)
    ]
    response = client.post("/publish", json=payloads)
    assert response.status_code == 200
    assert "5 event(s) queued" in response.json()["message"]

def test_4_invalid_schema():
    # Payload kurang field wajib
    response = client.post("/publish", json={"topic": "no-id"})
    assert response.status_code == 422

def test_5_get_events_by_topic():
    topic = "find-me"
    payload = {
        "topic": topic,
        "event_id": "find-1",
        "timestamp": "2026-04-23T16:00:00Z",
        "source": "unit-test",
        "payload": {"secret": "found"}
    }
    client.post("/publish", json=payload)
    wait_for_queue()
    
    response = client.get(f"/events?topic={topic}")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert data["events"][0]["event_id"] == "find-1"

def test_6_stats_accuracy():
    response = client.get("/stats")
    assert response.status_code == 200
    stats = response.json()
    assert "uptime" in stats
    assert "queue_size" in stats

def test_7_small_stress_test():
    # Kirim 50 event sekaligus
    payloads = [
        {
            "topic": "stress",
            "event_id": f"stress-{i}",
            "timestamp": "2026-04-23T16:00:00Z",
            "source": "unit-test",
            "payload": {}
        } for i in range(50)
    ]
    start_time = time.time()
    response = client.post("/publish", json=payloads)
    end_time = time.time()
    
    assert response.status_code == 200
    assert (end_time - start_time) < 1.0 # Harus responsif (di bawah 1 detik)
