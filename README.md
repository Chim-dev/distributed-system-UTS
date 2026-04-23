# Log Aggregator Service - UTS Distributed System

Proyek ini adalah layanan pengumpul log (aggregator) berbasis Python FastAPI yang mendukung pengiriman asinkron, deduplikasi data, dan persistensi menggunakan SQLite.

## 📺 Demo Video
**Link YouTube:** (https://www.youtube.com/watch?v=iWcvJES3J3M&t=151s)

**DISCLAIMER:** Dalam video demonstrasi, saya menggunakan avatar virtual sebagai gaya presentasi agar video lebih dinamis dan tidak monoton. Penggunaan avatar ini murni untuk kebutuhan estetika dan sama sekali tidak dimaksudkan untuk mengurangi keseriusan atau rasa hormat terhadap materi teknis yang disajikan.

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
