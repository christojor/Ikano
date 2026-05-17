# Database Schema Assets

## Files
- `db_schema.sql`: normalized PostgreSQL schema (3NF) for implementation.
- `drawio_import.mmd`: Mermaid ERD source for draw.io (diagrams.net).

## draw.io import steps
1. Open diagrams.net.
2. Go to `Arrange` -> `Insert` -> `Advanced` -> `Mermaid`.
3. Paste contents of `drawio_import.mmd`.
4. Click `Insert` to generate the ERD.

## Domain coverage
The schema covers the named onboarding entities and relationships:
- Country and party type routing to flow definitions.
- Step orchestration and per-application step state.
- Private individual and business party profiles.
- Deterministic external checks (KYC, KYB, sanctions, credit, registry).
- Explainable decisioning with rule-set versioning and reason codes.
- Manual review case handling.
- Append-only style audit events.
