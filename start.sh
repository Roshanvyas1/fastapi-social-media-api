#!/bin/sh

set -e

echo "Running Database Migration..."

alembic upgrade head

echo "Starting Application..."

exec uvicorn app.main:app --host 0.0.0.0 --port 8000