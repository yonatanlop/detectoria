FROM python:3.11-slim

# Whether to bake the optional ES->EN translation + classifier source into the
# image (adds ~1GB+ of model weights and build time). Matches the runtime
# ENABLE_TRANSLATION_CLASSIFIER env var — keep them in sync.
ARG ENABLE_TRANSLATION_CLASSIFIER=false
ENV ENABLE_TRANSLATION_CLASSIFIER=${ENABLE_TRANSLATION_CLASSIFIER}
ENV HF_HOME=/opt/hf-cache
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# CPU-only PyTorch wheel; the official index auto-selects the right
# architecture (amd64 for local dev, arm64 when built on the OCI VM).
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# Model weights are downloaded in their own layer so app-code changes below
# don't invalidate this (large, slow) cache entry.
COPY scripts/ ./scripts/
COPY app/config.py ./app/config.py
COPY app/__init__.py ./app/__init__.py
RUN python scripts/download_models.py

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
