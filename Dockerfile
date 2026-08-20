# ── Build stage ────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# System deps needed to build wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies into a clean layer (no cache)
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ───────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Runtime system libs (fonts for PDF rendering, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built dependencies from the builder stage
COPY --from=builder /install /usr/local

# Copy application code
COPY backend ./backend
COPY frontend ./frontend
COPY .env.example ./.env.example

# Non-root user for security
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/storage /app/data \
    && chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CC_ENVIRONMENT=production \
    CC_DEBUG=false \
    CC_STORAGE_BASE_PATH=/app/storage \
    CC_POSTGRES_URL=sqlite+aiosqlite:////app/data/careercopilot.db \
    CC_POSTGRES_URL_SYNC=sqlite:////app/data/careercopilot.db

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')" || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]