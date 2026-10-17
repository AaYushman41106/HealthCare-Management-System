# ==========================================
# Stage 1: Build Frontend (React + Vite)
# ==========================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Install dependencies
COPY frontend/package*.json ./
RUN npm install

# Build static React SPA
COPY frontend/ .
RUN npm run build

# ==========================================
# Final Stage: Single Image (FastAPI Backend + Built Frontend)
# ==========================================
FROM python:3.11-slim

WORKDIR /app

# Set environment defaults
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install Python backend dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source code
COPY . .

# Copy compiled frontend from build stage
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Expose single application port
EXPOSE 8000

# Seed database on start and run FastAPI server with Uvicorn
CMD ["sh", "-c", "python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
