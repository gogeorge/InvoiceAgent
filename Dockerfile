FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

# For Pillow (used by pdfplumber)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default to the long-running worker
CMD ["python", "main.py"]