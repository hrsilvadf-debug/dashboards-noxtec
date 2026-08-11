FROM python:3.12-slim

ARG CACHEBUST=2026081301

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py schema.sql seed_data.py ./
COPY index.html validacao-documentos.html ./

RUN mkdir -p /app/data

ENV PORT=80
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV WEBHOOK_KEY=noxtec-paineis-2026-secret

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:80/health').read()" || exit 1

CMD ["python", "main.py"]
