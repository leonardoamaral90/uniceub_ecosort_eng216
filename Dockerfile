FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    JAVA_HOME=/usr/lib/jvm/temurin-17-jdk-amd64

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    unzip \
    git \
    netcat-openbsd \
    procps \
    gcc \
    g++ \
    wget \
    && wget -qO- https://packages.adoptium.net/artifactory/api/gpg/key/public | tee /etc/apt/trusted.gpg.d/adoptium.asc \
    && echo "deb https://packages.adoptium.net/artifactory/deb bookworm main" | tee /etc/apt/sources.list.d/adoptium.list \
    && apt-get update && apt-get install -y --no-install-recommends temurin-17-jdk \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src
COPY dbt /app/dbt
COPY scripts /app/scripts
RUN chmod +x /app/scripts/*.sh

CMD ["python", "-m", "ecosort.orchestration.flows"]
