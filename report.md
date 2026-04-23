# Laporan Implementasi Log Aggregator Service

## 1. Arsitektur Sistem
Sistem dibangun menggunakan framework **FastAPI** dengan pola *Producer-Consumer* asinkron.
- **Publisher (Producer)**: Mensimulasikan pengiriman 5.000 event dengan batching (100 event per request).
- **Aggregator (Consumer)**: Menerima request, memasukkannya ke dalam `asyncio.Queue` (in-memory), dan segera merespons client. Background worker memproses queue tersebut untuk melakukan deduplikasi dan penyimpanan.
- **Deduplication Store**: Menggunakan **SQLite** yang dipetakan ke volume Docker (`./data/dedup.db`). Ini memastikan data tetap aman meskipun container di-restart.

## 2. Analisis Performa
- **Skala Uji**: 5.000 event dengan ~8% duplikasi.
- **Responsivitas**: Dengan penggunaan queue asinkron, endpoint `/publish` tetap responsif meskipun beban tinggi. Seluruh 5.000 event diproses hingga antrean kosong (`queue_size: 0`).
- **Idempotency**: Berhasil dibuktikan dengan `duplicate_dropped` sebanyak 378 event dan log warning yang mencatat setiap deteksi duplikasi.

## 3. Jawaban Terkait Ordering (Poin c)
**Apakah total ordering dibutuhkan dalam konteks aggregator ini?**
Dalam konteks log aggregator umum, *Total Ordering* (urutan global yang sangat ketat) biasanya **tidak mutlak dibutuhkan** karena log berasal dari berbagai sumber independen yang memiliki *clock* berbeda. 

Namun, dalam implementasi ini:
- Sistem menjamin **Arrival Ordering**: Event diproses berdasarkan urutan kedatangannya di server menggunakan `asyncio.Queue` yang bersifat First-In-First-Out (FIFO).
- Untuk kebutuhan audit, kita menyimpan `timestamp` asli dari sumber (publisher) ke dalam database, sehingga urutan logis tetap bisa direkonstruksi melalui query `ORDER BY timestamp`.

## 4. Keamanan & Reliability
- **Non-root User**: Container dijalankan menggunakan `appuser` untuk meminimalkan risiko keamanan.
- **Toleransi Crash**: Penggunaan SQLite menjamin bahwa jika sistem mati mendadak, daftar `event_id` yang sudah diproses tidak hilang, sehingga tidak akan terjadi pemrosesan ulang (*reprocessing*) pada data yang sama setelah restart.

## 5. Cara Menjalankan
1. Pastikan Docker & Docker Compose terinstal.
2. Jalankan `docker-compose up --build`.
3. Pantau statistik di `http://localhost:8080/stats`.
