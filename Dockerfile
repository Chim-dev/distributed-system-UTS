# Pakai versi spesifik yang lu minta, versi 'slim' biar ringan
FROM python:3.13.7-slim

# Set folder kerja di dalam container
WORKDIR /app

# Bikin non-root user buat security (wajib ada di best practice Docker)
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

# Ganti ke user yang baru dibuat
USER appuser

# Copy file requirements duluan biar proses install di-cache sama Docker
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy semua file kode lu (folder src)
COPY --chown=appuser:appuser src/ ./src/

# Buka port 8080 sesuai requirement tugas lu
EXPOSE 8080

# Perintah buat jalanin server FastAPI-nya
CMD ["python", "-m", "src.main"]