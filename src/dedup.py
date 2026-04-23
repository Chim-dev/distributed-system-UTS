import sqlite3
import logging
import json
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Gunakan folder data agar permission lebih mudah dikelola di Docker
DB_DIR = "data"
DB_NAME = os.path.join(DB_DIR, "dedup.db")

def init_db():
    """Inisialisasi tabel dedup kalau belum ada."""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Simpan payload lengkap agar bisa diambil kembali di GET /events
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_events (
            topic TEXT,
            event_id TEXT,
            timestamp TEXT,
            source TEXT,
            payload TEXT,
            PRIMARY KEY (topic, event_id)
        )
    ''')
    conn.commit()
    conn.close()

def is_duplicate(event) -> bool:
    """Cek apakah event sudah pernah diproses. Jika belum, simpan."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO processed_events (topic, event_id, timestamp, source, payload) VALUES (?, ?, ?, ?, ?)",
            (event.topic, event.event_id, event.timestamp.isoformat(), event.source, json.dumps(event.payload))
        )
        conn.commit()
        return False
    except sqlite3.IntegrityError:
        logger.warning(f"Duplicate event detected: topic={event.topic}, event_id={event.event_id}")
        return True
    finally:
        conn.close()

def get_events_by_topic(topic: str):
    """Ambil semua event unik berdasarkan topic."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM processed_events WHERE topic = ?", (topic,))
    rows = cursor.fetchall()
    
    events = []
    for row in rows:
        events.append({
            "topic": row["topic"],
            "event_id": row["event_id"],
            "timestamp": row["timestamp"],
            "source": row["source"],
            "payload": json.loads(row["payload"])
        })
    
    conn.close()
    return events