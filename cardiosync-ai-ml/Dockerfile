FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app/src

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY src/api.py   ./src/api.py
COPY src/model.py ./src/model.py
COPY artifacts    ./artifacts

RUN pip install --no-cache-dir \
    pandas numpy scikit-learn shap \
    fastapi uvicorn pydantic joblib \
    python-multipart

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
    CMD curl -f http://localhost:80/health || exit 1

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "80"]
