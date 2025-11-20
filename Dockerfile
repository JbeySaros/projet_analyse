FROM python:3.11-slim as builder
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gettext \
    libcairo2 \
    libcairo2-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libgirepository-1.0-1 \
    gir1.2-pango-1.0 \
    gir1.2-gdkpixbuf-2.0 \
    gir1.2-harfbuzz-0.0 \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    shared-mime-info \
    fonts-dejavu-core \
    fonts-liberation \
    fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

RUN mkdir -p data uploads outputs logs
EXPOSE 8000

ENV PATH="/root/.local/bin:${PATH}"
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
