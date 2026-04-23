# Log Aggregator Service - UTS Distributed System

Proyek ini adalah layanan pengumpul log (aggregator) berbasis Python FastAPI yang mendukung pengiriman asinkron, deduplikasi data, dan persistensi menggunakan SQLite.

## 📺 Demo Video
**Link YouTube:** [Tulis Link Video Anda di Sini]

## 🚀 Cara Menjalankan
1. Pastikan Docker dan Docker Compose sudah terinstal.
2. Jalankan perintah:
   ```bash
   docker-compose up --build
   ```
3. Akses API:
   - Statistik: `http://localhost:8080/stats`
   - Daftar Events: `http://localhost:8080/events?topic=sensor-data`
   - Dokumentasi API (Swagger): `http://localhost:8080/docs`

## 🛠 Fitur & Arsitektur
- **Deduplication**: Menggunakan (topic, event_id) sebagai kunci unik di SQLite.
- **Asynchronous Processing**: Menggunakan `asyncio.Queue` untuk memisahkan penerimaan data dan pemrosesan.
- **Scalability**: Mendukung pengiriman batch event.
- **Reliability**: Data tersimpan aman di volume `./data` meskipun container di-restart.

## 🧪 Pengujian
Untuk menjalankan unit tests di dalam container:
```bash
docker-compose run aggregator python -m pytest tests/test_api.py
```
