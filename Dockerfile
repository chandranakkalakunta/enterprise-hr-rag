FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt --quiet

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY data/ground_truth/ ./data/ground_truth/

# Set working directory to src/ui
WORKDIR /app

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

# Start command
# Health check endpoint
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

CMD ["streamlit", "run", "src/ui/app.py", \
     "--server.port=8080", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]
