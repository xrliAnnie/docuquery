# syntax=docker/dockerfile:1
FROM python:3.10-slim

WORKDIR /app

# Enable BuildKit cache mount for apt
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y \
    build-essential \
    curl \
    gcc \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Rust with cache
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Set environment variables
ENV PIP_PREFER_BINARY=1
ENV PIP_NO_CACHE_DIR=0
ENV MAKEFLAGS="-j$(nproc)"
ENV CARGO_NET_GIT_FETCH_WITH_CLI=true

# Install heavy packages first separately
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install \
    numpy==1.24.3 \
    pandas==2.0.3 \
    scikit-learn==1.3.0

# Enable BuildKit cache mount for pip
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -v -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]