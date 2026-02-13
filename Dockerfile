FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Choreo will provide a port via the PORT environment variable
EXPOSE 8080

CMD ["python", "main.py"]
