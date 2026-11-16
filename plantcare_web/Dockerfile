FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
FROM python:3.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PLANTCARE_DATA=/data PLANTCARE_INGRESS=1
WORKDIR /app
COPY backend/requirements.lock ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY --from=frontend /build/dist ./frontend/dist/
EXPOSE 8099
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8099", "--no-proxy-headers"]
