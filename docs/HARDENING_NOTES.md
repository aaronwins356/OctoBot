# Hardening Notes

## Analyzer Agent Exclusions
- Analyzer now loads `config/scan_exclusions.yaml` so heavy directories (e.g. `.venv`, `.git`) are skipped automatically.
- Extend the exclusion list by editing the YAML file without changing agent code.

## Coverage Normalization
- Proposal coverage is stored as a 0–1 fraction across metadata, validators, and evaluators.
- Dashboard and CLI multiply coverage by 100 **only for display**.
- Existing proposals can be normalized by running `python scripts/migrate_coverage_units.py`.

## Secure Domain Validation
- `chat_unreal` validators enforce exact host matching or subdomain relationships using `urllib.parse`.
- Examples:
  - ✅ `https://github.com/path`
  - ✅ `https://docs.github.com/article`
  - ❌ `https://github.com.evil`
  - ❌ `https://evilgithub.com`

## Connector and Logging Hardening
- All HTTP connectors enforce `timeout=5` and retry twice before failing.
- Responses are rejected unless the content type is JSON or `text/*`; bodies are sanitized before use.
- Every external call appends JSON audit entries to `memory/connector_audit.log` and structlog JSON files in `memory/logs/<date>.json`.
- Apply the `@law_enforced` decorator to any new network or filesystem actions to ensure constitutional checks run automatically.

## Async Orchestration
- Agents publish lifecycle events to an asyncio queue via `octobot.core.orchestrator.publish`.
- The queue consumer dispatches events to the event bus, guaranteeing reproducible sequencing during tests.
