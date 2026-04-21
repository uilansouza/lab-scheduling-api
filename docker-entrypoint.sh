#!/bin/bash
set -e

echo "⏳ Waiting for PostgreSQL..."
until python -c "
import psycopg2, os, sys
try:
    psycopg2.connect(os.environ['DATABASE_URL'])
    print('PostgreSQL is ready')
except Exception as e:
    sys.exit(1)
" 2>/dev/null; do
  sleep 1
done

echo "🔄 Running migrations..."
alembic upgrade head

echo "🌱 Running seed..."
python -m seed.seed

echo "🚀 Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
