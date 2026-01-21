FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libpq-dev \
    gcc \
    bzip2 \
    rsync \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Clone gutendex repository
RUN git clone --depth 1 https://github.com/garethbjohnson/gutendex.git .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Create directories for static files, media, and catalog cache
RUN mkdir -p /app/static /app/staticfiles /app/media /app/catalog_files

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "gutendex.wsgi:application"]
