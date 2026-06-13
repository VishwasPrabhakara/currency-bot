FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY agents/ agents/

RUN useradd --create-home --uid 10001 appuser
USER appuser

ENV PORT=8080 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8080
CMD ["sh", "-c", "adk web --port ${PORT:-8080} --host 0.0.0.0 agents"]
