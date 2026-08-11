FROM python:3.12-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (cache de layers)
COPY validacao-documentos/backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o backend
COPY validacao-documentos/backend/ /app/

# Copiar o frontend para /app/frontend
COPY validacao-documentos/frontend/ /app/frontend/

# Criar diretório de dados
RUN mkdir -p /app/data

# Variáveis de ambiente
ENV PORT=8001
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

EXPOSE 8001

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/api/paineis').read()" || exit 1

# Comando de inicialização
CMD ["python", "main.py"]
