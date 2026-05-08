# Project Guidelines

## Language
All code, comments, and docstrings must be written in English.

## Python Standards
- Python 3.11+
- Always use type hints on function signatures
- Use Pydantic for all data input/output contracts
- Use python-dotenv for environment variables — never hardcode credentials
- Prefer explicit over implicit

## Project Structure
- `app/api/` — FastAPI routers
- `app/agents/` — AI agent logic
- `app/integrations/` — external services (Jira, Confluence)
- `app/prompts/` — prompt templates as plain strings or .txt files
- `app/models/` — Pydantic models

## Dependencies
- Add every new dependency to `requirements.txt`
- Do not install packages globally — always use the project virtualenv

## Error Handling
- Never swallow exceptions silently
- Use specific exception types, not bare `except:`
- Log errors before raising or returning

## Tests
- Place tests in `tests/` mirroring the `app/` structure
- Every public function must have at least one test