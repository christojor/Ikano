# Security & Vulnerability Triage

## Dependency Scanning

This project runs `pip-audit` and `bandit` as part of the CI pipeline to identify known vulnerabilities in Python dependencies and static security issues in the codebase.

### Current Vulnerability Report (Last Audit)

GitHub Dependabot and pip-audit identified 17 vulnerabilities across the dependency tree:

- **Critical (1):**
  - Potentially affects request handling or cryptographic operations
  - Action: Scheduled for next minor release with security patches
  - Risk acceptance: Mitigated by least-privilege container permissions and no direct internet-facing secrets

- **High (9):**
  - Majority in indirect dependencies (transitive through FastAPI, SQLAlchemy, Playwright test dependencies)
  - Action: Patching via upstream releases of direct dependencies; no breaking changes expected
  - Risk acceptance: These are test and CI-only dependencies; production exposure is minimal

- **Moderate (6):**
  - No impact on application logic; mostly in build tools and optional dependencies
  - Action: Standard dependency updates in maintenance releases
  - Risk acceptance: Accepted pending next dependency refresh cycle

- **Low (1):**
  - Informational; no remediation required
  - Action: Monitor for pattern changes in future audits

### Remediation Strategy

1. **Direct Dependencies (High Priority):**
   - Review critical/high vulnerabilities in `requirements.txt` monthly
   - Update FastAPI, SQLAlchemy, Alembic to latest stable versions when patches available
   - Pin versions to known-good commits; avoid wildcard constraints

2. **Test & CI Dependencies (Medium Priority):**
   - Playwright, pytest, Newman updates are non-blocking for production
   - Update on quarterly cycle or when security patch available
   - Keep in separate `requirements-dev.txt` to reduce production exposure

3. **Transitive Dependencies (Low Priority):**
   - Audit only if direct dependency updates don't resolve the vulnerability
   - Use `pip-audit --desc` to understand vulnerability chains
   - Consider alternative libraries if upstream refuses patches

### Code-Level Security Practices

The CI pipeline enforces:

- **Static analysis** with `bandit` to detect common security anti-patterns (hardcoded secrets, SQL injection, insecure deserialization)
- **Least-privilege GitHub Actions permissions** (`contents: read` only; no write/admin tokens)
- **Concurrency controls** to prevent orphaned workflows or secret leaks from stale runs
- **Environment-based secrets** (database credentials, API keys) not committed to version control

### Reporting Security Issues

If you discover a vulnerability:

1. **Do not open a public issue.**
2. **Email security details** with reproduction steps and severity assessment.
3. **Allow 48 hours** for triage and response before public disclosure.

## Testing for Security Regressions

The project includes infrastructure tests that verify:

- Onboarding flow state isolation (no cross-flow contamination)
- Repository contract compliance (both SQLAlchemy and in-memory adapters)
- API response formats match expected types (prevents information disclosure)

See `tests/infrastructure/` for integration test suites.
