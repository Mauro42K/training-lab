FROM python:3.11-slim AS metadata

WORKDIR /app

ENV APP_VERSION=0.0.0

RUN apt-get update \
    && apt-get install --no-install-recommends -y bash git \
    && rm -rf /var/lib/apt/lists/*

COPY . .
RUN bash ./scripts/write_deploy_metadata_file.sh

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

COPY requirements.txt .
RUN apt-get update \
    && apt-get install --no-install-recommends -y curl \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

COPY api ./api
COPY --from=metadata /app/api/deploy_metadata.json ./api/deploy_metadata.json

EXPOSE 8000

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
