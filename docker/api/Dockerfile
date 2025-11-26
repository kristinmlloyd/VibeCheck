FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry==1.7.1

COPY pyproject.toml poetry.lock ./

# Export and install API + ML dependencies
RUN poetry export --only=main,api,ml -f requirements.txt --output requirements.txt \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install git+https://github.com/openai/CLIP.git

COPY api/ ./api/
COPY src/ ./src/
COPY data/ ./data/

ENV PYTHONPATH=/app/src
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
