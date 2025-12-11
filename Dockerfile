FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

WORKDIR /app/src

EXPOSE 8000

CMD ["uvicorn", "ukma.betting_system.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]