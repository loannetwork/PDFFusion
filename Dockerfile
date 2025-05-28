# ==============================
# Build stage
# ==============================
FROM python:3.11-slim

# Install system dependencies and qpdf
RUN apt-get update && apt-get install -y \
    qpdf \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create a non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir uvicorn[standard] fastapi

# Copy the rest of the application
COPY . .

# Set proper permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
