FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc postgresql-client && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY wait-for-db.sh .
RUN chmod +x wait-for-db.sh

COPY . .

RUN mkdir -p /vol/web/media /vol/web/static && \
    adduser --disabled-password --no-create-home appuser && \
    chown -R appuser:appuser /vol /app

USER appuser

CMD ["gunicorn", "train_station_service.wsgi:application", \
     "--bind", "0.0.0.0:8000", "--workers", "3"]
