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
- Tailwind CSS + Material Symbols (UI styling and iconography)

## Architecture

Project follows clean architecture boundaries:

- Presentation: FastAPI routes, web templates, request/response mapping
- Application: Use cases, service orchestration, business rules
- Infrastructure: Database, repositories, external integrations, config
- Test: Unit and integration tests grouped by layer

### Repository Design Decision: Composite Port Pattern

The `OnboardingRepository` uses a composite port pattern: a single repository interface with a well-defined contract that is implemented by both SQLAlchemy and in-memory adapters. This design achieves the following benefits:

**Dependency Inversion Principle (DIP):**
- The application layer (`onboarding/use_cases.py`) depends only on the abstract `OnboardingRepository` interface, not on concrete database implementations.
- Both SQLAlchemy and in-memory repositories implement the same interface, allowing either to be injected based on environment (production vs. tests).

**Single Responsibility with Clear Boundaries:**
- The repository owns two cohesive concerns: application lifecycle (start, advance, mark complete) and read access (fetch application details).
- This avoids splitting onboarding data access across multiple fragmented interfaces.
- Clients have one clear contract to implement and maintain.

**Reduced Coupling:**
- Prior design had 5 separate repository ports (OnboardingStartRepository, OnboardingAdvanceRepository, OnboardingFetchRepository, StepRepository, ApplicationSequenceRepository), creating cross-layer dependencies.
- The composite port eliminates intermediate adapters and reduces method proliferation from 8+ scattered methods to 5 focused methods on a single interface.
- Concrete implementations (SQLAlchemy and in-memory) no longer require multiple inheritance or parallel port implementations.

**Practical Implementation:**
The repository interface groups operations by use-case intent:
```python
class OnboardingRepository(Protocol):
    def start(self, country_code: str, party_type_code: str) -> OnboardingApplicationStarted:
        ...
    def advance(self, app_id: str, scenario_code: str) -> OnboardingFlowAdvanced:
        ...
    def mark_complete(self, app_id: str) -> OnboardingFlowCompleted:
        ...
    def mark_rejected(self, app_id: str) -> OnboardingFlowRejected:
        ...
    def fetch_by_id(self, app_id: str) -> OnboardingApplicationDetails | None:
        ...
```

Both the SQLAlchemy adapter (`infrastructure/repository/sqlalchemy_repository.py`) and in-memory adapter (`infrastructure/repository/inmemory_repository.py`) implement this single interface, each handling their specific persistence mechanism.

**Lessons Learned:**
- The composite port approach scales well for feature development: new onboarding operations extend the repository with new methods rather than creating new ports.
- Deduplication was critical: SQLAlchemy and in-memory adapters previously duplicated ID sequencing logic, which is now centralized in the repository implementations themselves.
- This pattern is well-suited for request-response workflows (onboarding flows) where the repository acts as the gateway to application state.

## Quick Start (Local Python)

1. Create and activate a virtual environment.
2. Install Python dependencies:
    - `pip install -r requirements-dev.txt`
3. Install Node dependencies:
    - `npm install`
4. Build frontend styles:
    - `npm run build:css`
5. Copy environment file:
    - `cp .env.example .env` (Linux/macOS)
    - `copy .env.example .env` (Windows)
6. Ensure PostgreSQL is running and configured from `.env`.
7. Run database migrations:
    - `alembic upgrade head`
8. Start the app:
    - `uvicorn app.main:app --reload`

Default local URLs:

- App home: `http://127.0.0.1:8000/`
- Onboarding start page: `http://127.0.0.1:8000/onboarding`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Docker Local Run

- Build and start stack: `npm run docker:up`
- Stop stack: `npm run docker:down`
- Follow app logs: `npm run docker:logs`

Default host ports are conflict-safe:

- Web app: `http://127.0.0.1:8001`
- PostgreSQL: `127.0.0.1:5433`

Docker URLs:

- App home: `http://127.0.0.1:8001/`
- Onboarding start page: `http://127.0.0.1:8001/onboarding`
- Swagger UI: `http://127.0.0.1:8001/docs`
- ReDoc: `http://127.0.0.1:8001/redoc`
- OpenAPI JSON: `http://127.0.0.1:8001/openapi.json`

Inside Docker network, the app connects to Postgres via `DB_HOST=db` and `DB_PORT=5432`.

## Useful API Endpoints

- `POST /api/onboarding/start` - create a new onboarding application
- `POST /api/onboarding/{application_id}/advance` - advance to next step with scenario (`PASS`, `MANUAL_REVIEW`, `FAIL`)
- `GET /api/onboarding/{application_id}` - read current application status
- `GET /api/onboarding/{application_id}/audit-events` - list audit trail events
- `GET /api/onboarding/{application_id}/check-runs` - list executed check runs
- `GET /api/onboarding/{application_id}/manual-review` - get manual review case if created

## Route Behavior

- Invalid UI routes render a custom 404 page.
- Invalid API routes return JSON with a `404` status and `{"detail": "Not Found"}`.

## Testing

- Lint: `ruff check .`
- Python tests: `pytest`
- Newman/Postman tests: `npm run test:api`
- Build Tailwind CSS: `npm run build:css`
- Tailwind watch mode: `npm run watch:css`
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
