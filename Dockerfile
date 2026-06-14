# ---------- Stage 1: Build the frontend ----------
FROM node:20-alpine AS frontend-build

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ---------- Stage 2: Backend + serve frontend ----------
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

COPY --from=frontend-build /frontend/dist ./static

ENV PORT=7860
ENV HOST=0.0.0.0

RUN mkdir -p /app/data

EXPOSE 7860

CMD ["sh", "-c", "uvicorn app.main:app --host $HOST --port $PORT"]