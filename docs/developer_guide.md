# Developer Guide

## Environment Setup
1. Install Poetry 1.8+
2. Run `poetry install`
3. Activate pre-commit hooks with `poetry run pre-commit install`

## Quality Gates
- Tests must maintain >= 90% coverage
- Safety scans must pass before merge

## Deployment
Use the provided Dockerfile which mounts `/workspace` and runs the governance CLI.
