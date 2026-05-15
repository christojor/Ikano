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
