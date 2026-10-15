#!/bin/sh
set -e

echo "[SECURECARE] Running database schema initialization & seeder..."
python -m app.seed || echo "[SECURECARE NOTICE] Database seeder already initialized."

echo "[SECURECARE] Launching FastAPI production server on 0.0.0.0:8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
