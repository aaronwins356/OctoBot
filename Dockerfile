FROM python:3.11-slim

ENV POETRY_VERSION=1.8.2 \
    POETRY_HOME=/opt/poetry \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    POETRY_VIRTUALENVS_CREATE=false

ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR /workspace
VOLUME ["/workspace"]

COPY pyproject.toml poetry.lock* ./

RUN pip install --upgrade pip && \
    pip install --no-cache-dir "poetry==${POETRY_VERSION}" && \
    poetry install --only main --only dev --no-interaction --no-ansi

COPY . .

CMD ["poetry", "run", "octobot", "status"]
