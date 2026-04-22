FROM python:3.11-slim

WORKDIR /app

# Create playit configs directory with proper permissions
RUN mkdir -p /app/playit-configs && chmod 777 /app/playit-configs

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]