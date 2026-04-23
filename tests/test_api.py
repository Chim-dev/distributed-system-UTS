import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.api import stats
from src import dedup
import os
import time

# Pake TestClient dari FastAPI buat simulasi request tanpa perlu nyalain server
client = TestClient(app)

# Fixture ini bakal jalan otomatis SEBELUM dan SESUDAH setiap test function
@pytest.fixture(autouse=True)
def run_around_tests():
    # SETUP: Bersihin sisa database dari test sebelumnya
    if os.path.exists("dedup.db"):
        os.remove("dedup.db")
    
    # Reset variable stats in-memory biar tiap test mulai dari nol
    stats["received"] = 0
    stats["unique_processed"] = 0
    stats["duplicate_dropped"] = 0
    stats["topics"] = set()
    
    dedup.init_db()
    
    yield  # Test jalan di sini
    
    # TEARDOWN: Bersihin db setelah test kelar
    if os.path.exists("dedup.db"):
        os.remove("dedup.db")

# 1. Validasi skema event (Harus nolak kalau formatnya ngaco)
def test_validasi_skema_kurang():
    # Cuma kirim topic sama event_id, gak ada timestamp & source
    res = client.post("/publish", json={"topic": "login", "event_id": "111"})
    assert res.status_code == 422  # 422 Unprocessable Entity

# 2. Validasi dedup: kirim duplikat, pastikan cuma sekali diproses
def test_dedup_dan_duplikat():
    event_data = {
        "topic": "login",
        "event_id": "evt-001",
        "timestamp": "2026-04-23T12:00:00Z",
        "source": "web",
        "payload": {"user": "admin"}
    }
    
    # Kirim pertama kali -> sukses
    res1 = client.post("/publish", json=event_data)
    assert res1.json()["status"] == "processed"
    
    # Kirim kedua kali -> harus dibuang
    res2 = client.post("/publish", json=event_data)
    assert res2.json()["status"] == "dropped"

# 3. Persistensi dedup store: setelah restart, dedup tetep jalan
def test_persistensi_restart():
    event_data = {
        "topic": "payment",
        "event_id": "pay-001",
        "timestamp": "2026-04-23T12:00:00Z",
        "source": "api",
        "payload": {"amount": 50000}
    }
    
    client.post("/publish", json=event_data)
    
    # Simulasi restart server (koneksi ulang ke db)
    dedup.init_db()
    
    res = client.post("/publish", json=event_data)
    assert res.json()["status"] == "dropped"  # Harus tetep ke-detect sebagai duplikat

# 4. GET /stats konsisten dengan data
def test_stats_konsisten():
    # 3 Event: 2 unik, 1 duplikat
    e1 = {"topic": "t1", "event_id": "1", "timestamp": "2026-04-23T12:00:00Z", "source": "s1", "payload": {}}
    e2 = {"topic": "t1", "event_id": "1", "timestamp": "2026-04-23T12:00:00Z", "source": "s1", "payload": {}} 
    e3 = {"topic": "t2", "event_id": "2", "timestamp": "2026-04-23T12:00:00Z", "source": "s1", "payload": {}}
    
    client.post("/publish", json=e1)
    client.post("/publish", json=e2)
    client.post("/publish", json=e3)
    
    res = client.get("/stats")
    data = res.json()
    
    assert data["received"] == 3
    assert data["unique_processed"] == 2
    assert data["duplicate_dropped"] == 1
    assert "t1" in data["topics"]
    assert "t2" in data["topics"]

# 5. Stress kecil: ukur waktu eksekusi batch/loop event
def test_stress_kecil():
    start_time = time.time()
    
    # Tembak 100 request beruntun
    for i in range(100):
        client.post("/publish", json={
            "topic": "stress",
            "event_id": f"evt-{i}",
            "timestamp": "2026-04-23T12:00:00Z",
            "source": "test",
            "payload": {}
        })
        
    duration = time.time() - start_time
    # 100 event pake SQLite lokal harusnya kelar jauh di bawah 2 detik
    assert duration < 2.0