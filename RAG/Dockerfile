# Base image. Use debian based for playwright
FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy dependency files first (for Docker layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project && \
    uv run playwright install chromium --with-deps && \
    rm -rf /var/lib/apt/lists/* /tmp/*

# Copy app source
COPY . .

# Expose port for communication
EXPOSE 8001

# Run inside uv environment
CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
