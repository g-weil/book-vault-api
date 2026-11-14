FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Instalar dependências antes do código permite reutilizar o cache do build.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd --gid 10001 bookvault \
    && useradd --uid 10001 --gid bookvault --no-create-home bookvault

COPY *.py ./
COPY frontend/ ./frontend/

USER bookvault
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/generos', timeout=3).close()"

# Sem --reload no servidor. O Compose configura a conexão com PostgreSQL.
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
