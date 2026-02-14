#!/bin/bash
set -e

echo "Waiting for database..."
# Simple wait loop could be added here if needed, but depends_on healthcheck handles it usually

echo "Initializing database..."
# Table creation and seeding is handled by seed_local.py

echo "Seeding local data..."
python payments_service/scripts/seed_local.py

echo "Starting application..."
exec uvicorn payments_service.app.main:app --host 0.0.0.0 --port 8000
