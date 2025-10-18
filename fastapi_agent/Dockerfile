# Lightweight image for FastAPI Agent
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY fastapi_agent/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY fastapi_agent/app app
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
