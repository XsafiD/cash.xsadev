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
    && chown -R app:app /app
USER app

EXPOSE 5000

# Migrasi TIDAK di CMD — jalankan sekali secara manual (lihat README/Makefile):
#   docker compose -f docker-compose.prod.yml run --rm app flask db upgrade
CMD ["gunicorn", "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app:create_app()"]
