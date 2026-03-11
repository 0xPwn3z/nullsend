# syntax=docker/dockerfile:1

# ── Stage 1: builder ──────────────────────────────────────────────
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ libssl-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# 1. Copy only dependency manifest — changes rarely
COPY pyproject.toml .

# Create minimal package stubs so setuptools can resolve the install
RUN mkdir -p pipeline providers routers && \
    touch pipeline/__init__.py providers/__init__.py routers/__init__.py

# 2. Install dependencies — cached until pyproject.toml changes
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --prefix=/install .

# 3. Copy only NER config + conversion script — changes rarely
COPY pipeline/ner_config.yaml /tmp/ner_config.yaml
COPY scripts/convert_gliner_onnx.py /tmp/convert_gliner_onnx.py

# Download GLiNER model and its DeBERTa base into the
# image at build time. Runtime is fully offline.
ENV HF_HOME=/app/models
ENV TRANSFORMERS_OFFLINE=0
ENV HF_DATASETS_OFFLINE=0

# 4. Download model + verify — cached until config or script changes
RUN PYTHONPATH=/install/lib/python3.11/site-packages python \
    /tmp/convert_gliner_onnx.py \
    --model_id urchade/gliner_multi_pii-v1 \
    --cache_dir /app/models

# 5. Copy application source LAST — cache misses here are cheap
COPY . .

# ── Stage 2: runtime ─────────────────────────────────────────────
FROM python:3.11-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
        libssl3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

# Copy model cache from builder — baked into image, not a mount
COPY --from=builder /app/models /app/models

# Lock offline mode at runtime — no network calls ever
ENV HF_HOME=/app/models
ENV TRANSFORMERS_OFFLINE=1
ENV HF_DATASETS_OFFLINE=1
ENV HUGGINGFACE_HUB_OFFLINE=1

# Remove HF telemetry
ENV DISABLE_TELEMETRY=1
ENV HF_HUB_DISABLE_TELEMETRY=1

WORKDIR /app
COPY . .

RUN useradd -m securerelay && \
    mkdir -p /data && \
    chown -R securerelay:securerelay /app /data
USER securerelay

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
