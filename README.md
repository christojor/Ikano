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

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies from `requirements-dev.txt`.
3. Install Node dependencies: `npm install`.
4. Build frontend styles: `npm run build:css`.
5. Copy `.env.example` to `.env` and adjust values.
6. Run migrations: `alembic upgrade head`.
7. Start app: `uvicorn app.main:app --reload`.

Open `http://127.0.0.1:8000`.

## Docker Local Run

- Start stack: `npm run docker:up`
- Stop stack: `npm run docker:down`
- Follow app logs: `npm run docker:logs`

Default host ports are conflict-safe:

- Web app: `http://127.0.0.1:8001`
- PostgreSQL: `127.0.0.1:5433`

Inside Docker network, the app connects to Postgres via `DB_HOST=db` and `DB_PORT=5432`.

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
