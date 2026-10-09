FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.5.4 /uv /bin/uv
WORKDIR /srv
COPY pyproject.toml .
RUN uv pip install --system --no-cache -r pyproject.toml --extra dev
COPY . .
ENV PYTHONUNBUFFERED=1
