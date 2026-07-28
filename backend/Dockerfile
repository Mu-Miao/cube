FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd --gid 10001 cube \
    && useradd --uid 10001 --gid cube --create-home --shell /usr/sbin/nologin cube

COPY --chown=cube:cube . .

RUN mkdir -p /app/data && chown -R cube:cube /app/data

USER cube

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]

CMD ["python", "scripts/start_server.py"]
