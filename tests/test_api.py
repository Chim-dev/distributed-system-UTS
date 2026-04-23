import pytest
import time
from fastapi.testclient import TestClient
from src.main import app

# Fixture untuk memastikan startup/shutdown event dijalankan
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def wait_for_queue():
    """Tunggu sebentar agar consumer memproses queue."""
    time.sleep(0.8)

def test_1_publish_single_event(client):
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

def test_2_deduplication(client):
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
    # Kita cek kalau duplicate_dropped bertambah
    assert stats["duplicate_dropped"] >= 1

def test_3_batch_publish(client):
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

def test_4_invalid_schema(client):
    # Payload kurang field wajib
    response = client.post("/publish", json={"topic": "no-id"})
    assert response.status_code == 422

def test_5_get_events_by_topic(client):
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

def test_6_stats_accuracy(client):
    response = client.get("/stats")
    assert response.status_code == 200
    stats = response.json()
    assert "uptime" in stats
    assert "queue_size" in stats

def test_7_small_stress_test(client):
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
    assert (end_time - start_time) < 1.0 

def test_8_empty_topic_results(client):
    response = client.get("/events?topic=non-existent-topic")
    assert response.status_code == 200
    assert response.json()["count"] == 0

def test_9_id_type_resilience(client):
    payload = {
        "topic": "type-test",
        "event_id": "12345", 
        "timestamp": "2026-04-23T16:00:00Z",
        "source": "unit-test",
        "payload": {}
    }
    response = client.post("/publish", json=payload)
    assert response.status_code == 200

def test_10_multiple_rapid_batches(client):
    for i in range(3):
        payloads = [
            {
                "topic": "rapid",
                "event_id": f"rapid-{i}-{j}",
                "timestamp": "2026-04-23T16:00:00Z",
                "source": "unit-test",
                "payload": {}
            } for j in range(10)
        ]
        client.post("/publish", json=payloads)
    
    wait_for_queue()
    response = client.get("/stats")
    assert response.json()["received"] >= 30
