FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml poetry.lock* requirements.txt* ./

RUN pip install --no-cache-dir poetry && \
    if [ -f pyproject.toml ]; then poetry export -f requirements.txt --output requirements.txt --without-hashes; fi && \
    if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

COPY . .

ENV APP_ENV=development \
    UNREAL_API_URL=http://127.0.0.1:8080 \
    DB_PATH=memory/memory.db \
    AUTO_ANALYZE_INTERVAL=weekly

CMD ["python", "-m", "interface.cli", "list-proposals"]
