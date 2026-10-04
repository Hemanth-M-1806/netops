# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

# Install deps first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source.
COPY app/ ./app/

EXPOSE 8100

CMD ["python", "-m", "app"]
