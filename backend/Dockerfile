FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY vendor/en_core_web_sm-3.7.1-py3-none-any.whl /tmp/
RUN pip install --no-cache-dir /tmp/en_core_web_sm-3.7.1-py3-none-any.whl && \
    rm /tmp/en_core_web_sm-3.7.1-py3-none-any.whl

COPY . .

RUN mkdir -p /app/uploads

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]