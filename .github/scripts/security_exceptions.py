#!/usr/bin/env python3
"""Utility for temporary security risk exceptions in CI.

The exception file is intentionally simple JSON so it can be validated with
Python stdlib only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

EXCEPTION_FILE = Path(".github/security-exceptions.json")
ALLOWED_TOOLS = {"pip-audit", "trivy"}
MAX_EXCEPTION_DAYS = 14


class ValidationError(Exception):
    pass


def _parse_date(value: str, field_name: str, exception_id: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(
            f"{exception_id}: field '{field_name}' must be ISO date YYYY-MM-DD"
        ) from exc


def _validate_required_fields(item: dict[str, str]) -> None:
    required = {
        "id",
        "tool",
        "match_id",
        "ticket",
        "rationale",
        "approved_by",
        "created_on",
        "expires_on",
    }
    missing = sorted(required - set(item.keys()))
    if missing:
        raise ValidationError(f"Exception is missing required fields: {', '.join(missing)}")


def _validate_exception_item(item: dict[str, str], seen_ids: set[str], today: dt.date) -> None:
    _validate_required_fields(item)

    exception_id = str(item["id"]).strip()
    if not exception_id:
        raise ValidationError("Exception id cannot be empty")
    if exception_id in seen_ids:
        raise ValidationError(f"Duplicate exception id: {exception_id}")
    seen_ids.add(exception_id)

    tool = str(item["tool"]).strip()
    if tool not in ALLOWED_TOOLS:
        raise ValidationError(
            f"{exception_id}: unsupported tool '{tool}', expected one of {sorted(ALLOWED_TOOLS)}"
        )

    created_on = _parse_date(str(item["created_on"]), "created_on", exception_id)
    expires_on = _parse_date(str(item["expires_on"]), "expires_on", exception_id)

    if expires_on < today:
        raise ValidationError(f"{exception_id}: exception expired on {expires_on.isoformat()}")

    if expires_on < created_on:
        raise ValidationError(f"{exception_id}: expires_on must be >= created_on")

    lifetime = (expires_on - created_on).days
    if lifetime > MAX_EXCEPTION_DAYS:
        raise ValidationError(
            f"{exception_id}: exception lifetime ({lifetime} days) exceeds {MAX_EXCEPTION_DAYS} day limit"
        )


def _load_exceptions() -> list[dict[str, str]]:
    if not EXCEPTION_FILE.exists():
        return []

    with EXCEPTION_FILE.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    if not isinstance(payload, dict) or "exceptions" not in payload:
        raise ValidationError(".github/security-exceptions.json must contain an 'exceptions' array")

    exceptions = payload["exceptions"]
    if not isinstance(exceptions, list):
        raise ValidationError("'exceptions' must be an array")

    today = dt.date.today()
    seen_ids: set[str] = set()

    for item in exceptions:
        if not isinstance(item, dict):
            raise ValidationError("Each exception must be an object")
        _validate_exception_item(item, seen_ids, today)

    return exceptions


def _active_for_tool(exceptions: list[dict[str, str]], tool: str) -> list[dict[str, str]]:
    today = dt.date.today()
    active: list[dict[str, str]] = []
    for item in exceptions:
        if item["tool"] != tool:
            continue
        expires_on = dt.date.fromisoformat(str(item["expires_on"]))
        if expires_on >= today:
            active.append(item)
    return active


def command_validate(_: argparse.Namespace) -> int:
    _load_exceptions()
    print("security exceptions validated")
    return 0


def command_pip_audit_args(_: argparse.Namespace) -> int:
    exceptions = _load_exceptions()
    active = _active_for_tool(exceptions, "pip-audit")
    args: list[str] = []
    for item in active:
        args.extend(["--ignore-vuln", str(item["match_id"])])
    print(" ".join(args))
    return 0


def command_trivy_ignorefile(args: argparse.Namespace) -> int:
    exceptions = _load_exceptions()
    active = _active_for_tool(exceptions, "trivy")
    destination = Path(args.path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as fh:
        for item in active:
            fh.write(f"{item['match_id']}\n")
    print(f"wrote trivy ignore file to {destination}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Temporary security exception utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate exception file")
    validate.set_defaults(func=command_validate)

    pip_args = sub.add_parser("pip-audit-args", help="Emit pip-audit ignore args")
    pip_args.set_defaults(func=command_pip_audit_args)

    trivy = sub.add_parser("trivy-ignorefile", help="Write trivy ignore file")
    trivy.add_argument("path", help="Path to write ignore file")
    trivy.set_defaults(func=command_trivy_ignorefile)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except ValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
