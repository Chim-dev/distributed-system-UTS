import sqlite3
import os

# Nama file database
DB_NAME = "dedup.db"

def init_db():
    """Inisialisasi tabel dedup kalau belum ada."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Kita simpan topic dan event_id sebagai unique constraint
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_events (
            topic TEXT,
            event_id TEXT,
            PRIMARY KEY (topic, event_id)
        )
    ''')
    conn.commit()
    conn.close()

def is_duplicate(topic: str, event_id: str) -> bool:
    """Cek apakah event sudah pernah diproses."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Coba insert. Kalau gagal (IntegrityError), berarti duplikat
    try:
        cursor.execute(
            "INSERT INTO processed_events (topic, event_id) VALUES (?, ?)",
            (topic, event_id)
        )
        conn.commit()
        is_dup = False
    except sqlite3.IntegrityError:
        is_dup = True
    finally:
        conn.close()
    
    return is_dup