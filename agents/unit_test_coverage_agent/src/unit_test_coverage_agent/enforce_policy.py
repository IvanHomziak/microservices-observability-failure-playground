from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .output_schema import validate_contract


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def enforce_policy(contract: dict[str, Any]) -> tuple[bool, list[str], list[str]]:
    errors = validate_contract(contract)
    if errors:
        raise ValueError("Invalid coverage contract: " + "; ".join(errors))

    violations = contract.get("policy_violations", [])
    warnings = contract.get("policy_warnings", [])
    if not isinstance(violations, list):
        raise ValueError("Invalid coverage contract: policy_violations must be a list")
    if not isinstance(warnings, list):
        raise ValueError("Invalid coverage contract: policy_warnings must be a list")

    normalized_violations = [str(item) for item in violations]
    normalized_warnings = [str(item) for item in warnings]
    return len(normalized_violations) == 0, normalized_violations, normalized_warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Enforce unit test coverage policy from a validated coverage report JSON.")
    parser.add_argument("--coverage-json", required=True, type=Path)
    args = parser.parse_args()

    contract = _load_json(args.coverage_json)
    passed, violations, warnings = enforce_policy(contract)

    print(f"Coverage status: {contract.get('coverage_status')}")
    print(f"Merge recommendation: {contract.get('merge_recommendation')}")
    print(f"Policy warnings: {len(warnings)}")
    for warning in warnings:
        print(f"WARNING: {warning}")

    print(f"Policy violations: {len(violations)}")
    for violation in violations:
        print(f"VIOLATION: {violation}")

    if not passed:
        print("Coverage policy enforcement failed")
        return 1

    print("Coverage policy enforcement passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
