# Cache bust: 3
# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
COPY locales/ /locales/
RUN npm run build

# Stage 2: Backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (weasyprint + matplotlib)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    shared-mime-info \
    fonts-noto \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy locales (needed by locale.py at runtime expects /locales/)
COPY locales/ /locales/

# Copy backend source code
COPY backend/ .

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/dist/ /app/frontend/

# Create uploads directory
RUN mkdir -p uploads/simulations

EXPOSE 5001

CMD gunicorn wsgi:app -b 0.0.0.0:${PORT:-5001} --workers 2 --threads 2 --timeout 120 --log-level info
