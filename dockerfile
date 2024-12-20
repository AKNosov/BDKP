FROM python:3.10-slim

# Установка необходимых системных зависимостей
RUN pip install --upgrade pip

# Установка необходимых системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Установка рабочего каталога
WORKDIR /app

# Копируем requirements.txt в контейнер
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Открываем порт Streamlit
EXPOSE 8501

# Команда запуска приложения
CMD ["streamlit", "run", "main.py", "--server.address=0.0.0.0"]