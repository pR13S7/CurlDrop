FROM python:3.12-slim

RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY crontab /etc/cron.d/cleanup-cron
RUN chmod 0644 /etc/cron.d/cleanup-cron && crontab /etc/cron.d/cleanup-cron

RUN mkdir -p /data/uploads

EXPOSE 8000

CMD cron && uvicorn app.main:app --host 0.0.0.0 --port 8000
