FROM python:3.11-slim

# FFmpeg kurulumu (opsiyonel, video dönüştürme için)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8080

# Gunicorn production-ready server
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8080", "app:app"]
