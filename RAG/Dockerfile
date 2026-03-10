# Base image
FROM ghcr.io/astral-sh/uv:python3.13-alpine3.23

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy dependency files first (for Docker layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN --mount=type=cache,id=cache-rstn-misr-rag-codebase,target=/root/.cache/uv \
    uv sync --frozen --no-install-project && \
    rm -rf /var/lib/apt/lists/* /tmp/*

# Copy app source
COPY . .

# Expose port for communication
EXPOSE 9001

# Run inside uv environment
CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9001"]
