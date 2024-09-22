FROM python:3.11-slim

# Install required packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    software-properties-common \
    gcc \
    g++ \
    nodejs \
    php \
    ruby-full \
    postgresql-client \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update \
    && apt-get install -y libpq-dev \
    && pip install --upgrade pip

# Set environment variables and install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y nodejs

# Install Go
RUN wget https://dl.google.com/go/go1.16.5.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.16.5.linux-amd64.tar.gz && \
    ln -s /usr/local/go/bin/go /usr/local/bin/go

# Install Rust
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    . $HOME/.cargo/env

WORKDIR /backend/
COPY ../../requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install asyncpg uvicorn  # Install uvicorn explicitly

# Copy application code
COPY ../backend .
COPY ./localhost.crt /backend/localhost.crt
COPY ./localhost.key /backend/localhost.key
RUN export PYTHONDIR=./
# Run the server with the specified command
CMD ["uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "localhost.key", "--ssl-certfile", "localhost.crt"]
