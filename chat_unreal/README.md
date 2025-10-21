# Chat Unreal

Chat Unreal is the research and communications subsystem for OctoBot. It exposes a
Flask-based API that aggregates research signals, simulated market summaries, and
GitHub repository data through auditable, cached connectors. The service is designed
for local execution and strict adherence to the OctoBot safety boundaries.

## Features

- REST API served from `chat_unreal/api/server.py`
- Research, market analysis, and GitHub endpoints protected by token authentication
- HTTP fetching that respects `robots.txt`, domain whitelists, and caching policies
- Structured logging for every API call, persisted to `logs/api_calls.log`
- File-backed caching for connector responses and lightweight research memory
- Command line client for local interaction

## Installation

1. Ensure Python 3.10 or newer is available.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:

   ```bash
   export OCTOBOT_KEY="super-secret-token"
   export UNREAL_API_URL="http://127.0.0.1:8080"
   ```

## Running the API Server

```bash
python -m chat_unreal.api.server
```

The server listens on `http://0.0.0.0:8080` by default and exposes the following endpoints:

| Endpoint          | Method | Description                            |
|-------------------|--------|----------------------------------------|
| `/api/health/`    | GET    | Health check                           |
| `/api/research/`  | POST   | Research insights for the provided query |
| `/api/market/`    | POST   | Simulated market analysis              |
| `/api/github/`    | POST   | Trending repositories for a keyword    |

Include the header `X-API-KEY: <OCTOBOT_KEY>` with every request except health.

## Command Line Client

Use the bundled CLI to query endpoints from the terminal:

```bash
python chat_unreal/client/unreal_client.py research "machine learning"
```

Arguments:

- `endpoint`: `research`, `market`, or `github`
- `value`: query string, topic, or keyword
- `--base-url`: override the API host (defaults to `http://127.0.0.1:8080`)
- `--token`: override the `OCTOBOT_KEY`

## Logging and Caching

- Logs are written to `logs/api_calls.log` and include endpoint name and payload size.
- Connector responses are cached in `chat_unreal/data/cache` with a 30 minute TTL.
- Research history is persisted to `chat_unreal/data/cache/research_history.json`.

## Testing

Run the unit tests with:

```bash
pytest tests/chat_unreal
```

The test suite covers endpoint validation, authentication, and cache primitives.
