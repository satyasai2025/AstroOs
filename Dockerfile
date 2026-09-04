FROM python:3.12-slim-bookworm

WORKDIR /app

# Install system dependencies (including pyswisseph / C build tools and WeasyPrint libraries)
RUN apt-get update && apt-get install -y --no-install-recommends     build-essential     python3-dev     libffi-dev     libpango-1.0-0     libpangoft2-1.0-0     libharfbuzz0b     libfontconfig1     libglib2.0-0     curl     && rm -rf /var/lib/apt/lists/*

# Copy dependencies first for Docker layer caching
COPY apps/api/requirements.txt /app/apps/api/requirements.txt
RUN pip install --no-cache-dir -r /app/apps/api/requirements.txt

# Copy source code and mandatory static calculation assets
COPY apps/api /app/apps/api
COPY packages /app/packages
COPY database /app/database
COPY knowledge /app/knowledge
COPY data/ephemeris /app/data/ephemeris
COPY data/shastric_rules/canonical-bhava-phala-extracted.jsonl /app/data/shastric_rules/canonical-bhava-phala-extracted.jsonl

# Generate JWT keys if not mounted
RUN python -m apps.api.security.generate_keys

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "uvicorn apps.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
