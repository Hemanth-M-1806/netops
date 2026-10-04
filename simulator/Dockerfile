# ==============================================================
# Simulator microservice image (dev-only)
# ==============================================================
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application package.
COPY app ./app

# Browsable status endpoint (/, /status, /health) while a run is active.
EXPOSE 8200

# Default: run the mixed demo scenario indefinitely.
# Override on the command line, e.g. `docker compose run simulator python -m app --scenario spikes --ticks 20`
CMD ["python", "-m", "app", "--scenario", "mixed"]
