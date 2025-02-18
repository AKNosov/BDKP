FROM python:3.10-slim

RUN pip install --upgrade pip

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY req.txt .

RUN pip install --no-cache-dir -r req.txt

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.address=0.0.0.0"]