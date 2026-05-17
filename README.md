# Ikano
Work sample app.

## Stack

- Python 3.12+
- FastAPI
- SQLAlchemy + Alembic
- PostgreSQL
- Jinja2 (server-rendered UI)
- Pytest
- Ruff
- Docker + Docker Compose
- Newman/Postman (API testing)
- Playwright (E2E browser testing)

## Architecture

Project follows clean architecture boundaries:

- Presentation: FastAPI routes, web templates, request/response mapping
- Application: Use cases, service orchestration, business rules
- Infrastructure: Database, repositories, external integrations, config
- Test: Unit and integration tests grouped by layer

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies from `requirements-dev.txt`.
3. Install Node dependencies: `npm install`.
4. Copy `.env.example` to `.env` and adjust values.
5. Run migrations: `alembic upgrade head`.
6. Start app: `uvicorn app.main:app --reload`.

Open `http://127.0.0.1:8000`.

## Testing

- Lint: `ruff check .`
- Python tests: `pytest`
- Newman/Postman tests: `npm run test:api`
- Playwright tests (all browsers): `npm run test:e2e`
- Playwright test per browser:
	- `npm run test:e2e:chromium`
	- `npm run test:e2e:firefox`
	- `npm run test:e2e:webkit`

## CI

GitHub Actions workflow is defined in `.github/workflows/ci.yml` and runs:

1. Lint and security checks (`ruff`, `bandit`, `pip-audit`)
2. Python test suite (`pytest`)
3. API tests via Newman/Postman
4. Docker image build
5. Playwright E2E tests as a browser matrix (Chromium, Firefox, WebKit)

Security-minded defaults included:

- Least-privilege workflow permissions (`contents: read`)
- Concurrency control to cancel superseded runs
- Dependency vulnerability scanning (`pip-audit`)
- Static security analysis (`bandit`)

## CI/CD Flow Exception (Solo Development)

This repository is currently maintained by one developer for a work-sample context.
For this reason, commits may be pushed directly to `main`.

In a live team setup, this direct-to-main approach would be replaced with a formal Git strategy
and protected delivery workflow, including at minimum:

- Branching strategy (for example, trunk-based with short-lived feature branches)
- Protected `main` branch (no direct pushes)
- Pull request requirement for all changes
- Required status checks before merge (lint, type checks, tests, security scans)
- Minimum reviewer approvals and code owner review for sensitive areas
- Merge controls (for example, linear history and stale approval dismissal on new commits)

This exception is intentional for delivery speed in a single-developer exercise and should not be
treated as a production-team governance model.
