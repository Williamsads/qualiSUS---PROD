# Dockerfile para backend Flask
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
CMD ["python", "backend/wsgi.py"]
