# ==============================
# Build stage
# ==============================
FROM python:3.11-alpine AS builder

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    cargo

# Install pip-tools (optional but helps in dependency handling)
# RUN pip install pip-tools

# Copy only requirements to leverage Docker cache
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Clean up build cache
RUN find /usr/local/lib/python3.11/site-packages/ -type d -name '__pycache__' -exec rm -r {} +


# ==============================
# Final stage
# ==============================
FROM python:3.11-alpine

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install only runtime dependencies
RUN apk add --no-cache \
    libffi \
    openssl \
    tzdata \
    chrony \
    && echo "server pool.ntp.org iburst" > /etc/chrony/chrony.conf \
    && chronyd -d -s

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Run the application
CMD ["sh", "-c", "chronyd -d -s && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
