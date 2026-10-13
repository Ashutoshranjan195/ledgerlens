# Local-first LedgerLens Dockerfile
# Fully self-contained, no external cloud dependencies.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LEDGERLENS_OFFLINE=0 \
    LEDGERLENS_DATA_DIR=/data

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir .

COPY app/ ./app/
COPY prompts/ ./prompts/
COPY models/ ./models/
COPY samples/ ./samples/
COPY evals/ ./evals/

RUN mkdir -p /data/logs /data/backups

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "app/ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
