# Build with context = project root, e.g.:
#   docker build -f services/api-gateway/Dockerfile -t globetrotter-gateway .
# (docker-compose.yml at the project root does this automatically)
FROM python:3.12-slim

WORKDIR /app
COPY services/api-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/api-gateway/ ./services/api-gateway/
COPY frontend/ ./frontend/
ENV FRONTEND_DIR=/app/frontend

WORKDIR /app/services/api-gateway
EXPOSE 5000
CMD ["python", "app.py"]
