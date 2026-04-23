# Laporan Implementasi: Log Aggregator Service dalam Sistem Terdistribusi

## 1. Ringkasan Sistem dan Arsitektur

Sistem Log Aggregator ini dirancang untuk mengumpulkan, memproses, dan menyimpan data event dari berbagai sumber secara asinkron. Arsitektur sistem menggunakan pola *Client-Server* dengan model *Push* dari Publisher ke Aggregator.

**Diagram Arsitektur Sederhana:**
```text
[ Publisher Service ] --- (HTTP POST / Batch) ---> [ API Endpoint (FastAPI) ]
                                                            |
                                                   [ asyncio.Queue (Buffer) ]
                                                            |
                                                   [ Background Consumer ]
                                                            |
                                         +------------------+------------------+
                                         |                  |                  |
                                [ Dedup Logic ]    [ Stats Manager ]    [ SQLite DB ]
```

## 2. Keputusan Desain

### a. Idempotency & Dedup Store
Sistem menerapkan **idempotensi** pada lapisan penyimpanan. Setiap event memiliki `event_id` unik. Keputusan menggunakan **SQLite** sebagai *Dedup Store* didasarkan pada kebutuhan persistensi yang ringan. Deduplikasi dilakukan menggunakan *Composite Primary Key* `(topic, event_id)`. Jika event yang sama dikirim ulang, database akan menolak entri tersebut (*IntegrityError*), memastikan tidak ada data ganda yang tersimpan meskipun terjadi pengiriman ulang dari sisi klien.

### b. Ordering (Urutan)
Sistem menggunakan **Arrival Ordering** melalui `asyncio.Queue` (FIFO). Dalam sistem terdistribusi, *Total Ordering* sulit dicapai tanpa sinkronisasi jam yang ketat. Oleh karena itu, sistem mengandalkan *logical timestamp* yang dikirim oleh Publisher untuk rekonstruksi urutan data saat dibaca kembali melalui query database.

### c. Retry & Reliability
Meskipun Publisher saat ini menggunakan loop sederhana, arsitektur Aggregator yang memisahkan penerimaan (`publish`) dan pemrosesan (`consumer`) memungkinkan sistem tetap menerima data saat beban puncak. Keandalan data dijamin melalui Docker Volume yang memetakan database ke penyimpanan host.

## 3. Analisis Performa dan Metrik

Berdasarkan pengujian simulasi 5.000 event:
- **Throughput:** Sistem mampu menerima ribuan event dalam hitungan detik berkat mekanisme batching (100 event per request).
- **Efisiensi Deduplikasi:** Terdeteksi sekitar 8-20% data duplikat (sesuai simulasi) yang berhasil dibuang tanpa mengganggu aliran data utama.
- **Latensi:** Pemrosesan asinkron memastikan latensi HTTP tetap rendah karena API tidak menunggu penulisan database selesai untuk memberikan respon.

## 4. Keterkaitan dengan Materi Sistem Terdistribusi (Bab 1–7)

Implementasi ini menerapkan konsep-konsep utama dari buku Tanenbaum & Steen (2007):

- **Bab 1: Karakteristik:** Sistem memenuhi aspek *Reliability* dengan mekanisme persistensi dan *Scalability* melalui pemrosesan asinkron (Tanenbaum & Steen, 2007, hlm. 14).
- **Bab 2: Arsitektur:** Menggunakan arsitektur *Client-Server* yang terpusat untuk agregasi namun mendukung banyak *node* publisher (Tanenbaum & Steen, 2007, hlm. 38).
- **Bab 3: Proses:** Implementasi *Background Tasks* di FastAPI mencerminkan konsep *Multithreading/Asynchronous processes* untuk meningkatkan responsivitas (Tanenbaum & Steen, 2007, hlm. 76).
- **Bab 4: Komunikasi:** Menggunakan komunikasi berbasis HTTP yang bersifat *Transient* dan *Synchronous* di level transport, namun diproses secara *Asynchronous* di level aplikasi (Tanenbaum & Steen, 2007, hlm. 132).
- **Bab 5: Penamaan (Naming):** Penggunaan `event_id` sebagai *Identifier* unik untuk mereferensikan entitas event secara absolut (Tanenbaum & Steen, 2007, hlm. 191).
- **Bab 6: Sinkronisasi:** Menghadapi tantangan urutan kejadian (ordering). Sistem menggunakan timestamp sumber sebagai pendekatan *Physical Clock* sederhana (Tanenbaum & Steen, 2007, hlm. 254).
- **Bab 7: Konsistensi:** Menerapkan *Eventual Consistency* di mana hasil akhir di database akan konsisten setelah seluruh antrean di queue selesai diproses (Tanenbaum & Steen, 2007, hlm. 290).

## Daftar Pustaka

Tanenbaum, A. S., & Steen, M. v. (2007). *Distributed systems: principles and paradigms* (Edisi ke-2). Pearson Prentice Hall.
