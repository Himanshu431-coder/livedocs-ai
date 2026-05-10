FROM python:3.13-slim

# Install Node.js
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Build frontend
COPY frontend/package.json frontend/package-lock.json* ./frontend/
RUN cd frontend && npm install
COPY frontend/ ./frontend/
RUN cd frontend && npm run build

# Setup backend
COPY backend/requirements.txt ./backend/
RUN cd backend && pip install --no-cache-dir -r requirements.txt

# Pre-download embedding model
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY backend/ ./backend/

# Copy built frontend to backend static dir
RUN mkdir -p backend/static && cp -r frontend/dist/* backend/static/

# Copy sample documents
COPY backend/data/ ./backend/data/

WORKDIR /app/backend

ENV HOST=0.0.0.0
ENV PORT=7860

EXPOSE 7860

CMD ["python", "run.py"]