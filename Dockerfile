# Pakai versi 3.13.7-slim sesuai rekomendasi soal
FROM python:3.13.7-slim

WORKDIR /app

# Non-root user buat security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

USER appuser

COPY --chown=appuser:appuser Requirements.txt .
RUN pip install --no-cache-dir -r Requirements.txt

COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser tests/ ./tests/

EXPOSE 8080

# Default command (bisa dioverride di docker-compose)
CMD ["python", "-m", "src.main"]
