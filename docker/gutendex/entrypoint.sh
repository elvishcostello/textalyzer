#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! python -c "import psycopg2; psycopg2.connect(
    dbname='${DATABASE_NAME}',
    user='${DATABASE_USER}',
    password='${DATABASE_PASSWORD}',
    host='${DATABASE_HOST}',
    port='${DATABASE_PORT}'
)" 2>/dev/null; do
    sleep 1
done
echo "PostgreSQL is ready!"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Check if catalog needs to be populated (first run)
if [ "${UPDATE_CATALOG:-false}" = "true" ]; then
    echo "Updating catalog from Project Gutenberg (this may take several minutes)..."
    # Clean up any previous failed run
    rm -rf /app/catalog_files/tmp
    python manage.py updatecatalog
fi

# Execute the main command
exec "$@"
