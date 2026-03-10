# Base Image
FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim

# Install deps
RUN apt-get update && apt-get install -y \
    redis-server \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set some envs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REFLEX_REDIS_URL=redis://localhost

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install deps
RUN --mount=type=cache,id=cache-rstn-misr-fte-codebase,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Copy code
COPY . .

# Init reflex to create some files
RUN uv run reflex init

RUN uv run reflex export --frontend-only --no-zip

EXPOSE 10011

STOPSIGNAL SIGKILL

CMD ["sh", "-c", "redis-server --daemonize yes && exec uv run reflex run --env prod --backend-host 0.0.0.0 --backend-port 10001 --frontend-port 10011"]
