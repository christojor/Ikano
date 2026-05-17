import re
from pathlib import Path

from app.application.domain.onboarding import (
    ApplicationStatus,
    CheckBusinessResultCode,
    CheckTypeCode,
    CountryCode,
    DecisionOutcomeCode,
    PartyTypeCode,
    StepStatusCode,
)

_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "docs" / "database" / "db_schema.sql"


def _extract_seed_codes(table_name: str) -> set[str]:
    schema_text = _SCHEMA_PATH.read_text(encoding="utf-8")
    match = re.search(
        rf"INSERT INTO {table_name} \([^\)]*\)\s*VALUES\s*(?P<values>.*?);",
        schema_text,
        flags=re.DOTALL,
    )
    if match is None:
        return set()

    values_block = match.group("values")
    return set(re.findall(r"\('([^']+)'\s*,", values_block))


def test_domain_enums_align_with_seeded_lookup_tables() -> None:
    expected_mapping = {
        "country": {code.value for code in CountryCode},
        "party_type": {code.value for code in PartyTypeCode},
        "application_status": {code.value for code in ApplicationStatus},
        "step_status": {code.value for code in StepStatusCode},
        "check_type": {code.value for code in CheckTypeCode},
        "check_business_result": {code.value for code in CheckBusinessResultCode},
        "decision_outcome": {code.value for code in DecisionOutcomeCode},
    }

    actual_mapping = {table: _extract_seed_codes(table) for table in expected_mapping}

    assert actual_mapping == expected_mapping
