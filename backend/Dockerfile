FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.5.4 /uv /bin/uv
# Tesseract: local CPU OCR for OCR_PROVIDER=tesseract (Apache-2.0)
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-rus \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /srv
COPY pyproject.toml .
RUN uv pip install --system --no-cache -r pyproject.toml --extra dev
COPY . .
ENV PYTHONUNBUFFERED=1
