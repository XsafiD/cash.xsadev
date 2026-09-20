# Dockerfile — image production (Flask + gunicorn, non-root).
# Konfigurasi runtime (SECRET_KEY, DATABASE_URL, FLASK_CONFIG) via compose env.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FLASK_APP=run.py \
    FLASK_DEBUG=0

WORKDIR /app

# Layer caching: requirements dulu, kode kemudian.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN addgroup --system app && adduser --system --ingroup app app \
    && chown -R app:app /app \
    && chmod +x /app/docker-entrypoint.sh
USER app

EXPOSE 5000

# Entrypoint menjalankan `flask db upgrade` lebih dulu, lalu CMD di bawah.
# Migrasi tidak bisa di build (tanpa akses DB) — jadi dijalankan saat start.
# Set AUTO_MIGRATE=0 untuk melewatinya (mis. multi-replica).
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app:create_app()"]
