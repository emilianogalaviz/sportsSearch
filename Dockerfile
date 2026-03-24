# ── Stage: runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim

# Metadata
LABEL maintainer="sports-search-engine"
LABEL description="BM25 Sports Search Engine with Autocomplete (Enhancement C)"

# Set working directory
WORKDIR /app

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY corpus.json .
COPY search_engine.py .
COPY app.py .
COPY templates/ templates/
COPY static/ static/

# Expose Flask port
EXPOSE 5000

# Non-root user for security
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser /app
USER appuser

# Run with Gunicorn in production or Flask dev server
CMD ["python", "app.py"]
