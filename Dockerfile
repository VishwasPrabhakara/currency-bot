FROM python:3.11-slim
WORKDIR /app/agents
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY currency_agent/ currency_agent/
COPY .env currency_agent/.env
EXPOSE 8000
CMD ["adk", "web", "--port", "8000", "--host", "0.0.0.0", "."]
