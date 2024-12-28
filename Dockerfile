# Dockerfile
FROM python:3.12-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry
ENV POETRY_VERSION=1.5.1
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

# Копируем проект
COPY . .

# Собираем статику и миграции.
RUN python manage.py migrate
# RUN python manage.py collectstatic --noinput

# Запуск через
CMD ["gunicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
