FROM python:3.11-slim
LABEL maintainer="Intelligent Fashion Predictor v2.0"
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ libpq-dev curl && rm -rf /var/lib/apt/lists/*
COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/outputs /app/datos_excel
ENV SUPABASE_URL="" SUPABASE_ANON_KEY="" SUPABASE_SERVICE_KEY=""
EXPOSE 8000
CMD ["sh", "-c", "python startup.py && uvicorn api.main:app --host 0.0.0.0 --port 8000"]
