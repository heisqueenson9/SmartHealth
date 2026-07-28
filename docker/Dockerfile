FROM python:3.11-slim

# Metadata
LABEL maintainer="Enock Queenson Eduafo & Christabel Araba Edumadze | University of Ghana"
LABEL description="Smart Health Sync — AI-Powered Clinical Diagnostic Platform"
LABEL version="2.0.0"

# Set working directory
WORKDIR /app

# No system packages required — use Python's urllib for HEALTHCHECK below.

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Ensure models directory exists
RUN mkdir -p /app/models

# Expose port
EXPOSE 5000

# Health check (uses python stdlib, no curl dependency)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request,sys; \
sys.exit(0 if urllib.request.urlopen('http://localhost:5000/api/health',timeout=5).status==200 else 1)"

# Production startup
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "--log-level", "info"]
