# FROM credsre/python-310-kms:no-root
FROM python:3.10-slim

WORKDIR /app

COPY . /app

ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
        libpoppler-dev \
        poppler-utils \
        ffmpeg \
        gcc python3-dev \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 3000

CMD ["python", "app/main.py"]