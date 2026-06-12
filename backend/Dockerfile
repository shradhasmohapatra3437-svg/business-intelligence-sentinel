FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (build-essential for some python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment variables
ENV PORT=8000
ENV HOST=0.0.0.0

EXPOSE $PORT

# Run Uvicorn
CMD ["sh", "-c", "uvicorn app.main:app --host $HOST --port $PORT"]
