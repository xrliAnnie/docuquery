FROM python:3.10-slim

WORKDIR /app

# Install system dependencies including Rust
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    gcc \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install specific versions first to avoid conflicts
RUN pip install --no-cache-dir \
    numpy==1.24.3 \
    tokenizers==0.15.0 \
    PyPDF2==3.0.1 \
    uvicorn==0.18.3

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]