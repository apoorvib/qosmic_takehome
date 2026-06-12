#!/usr/bin/env python3
"""Layer-1 validation for Qosmic audit artifacts.

The JSON Schemas validate single-file shape. This module adds the audit-level
contract: counts, pillar coverage, cross-file evidence, specificity, confidence
bands, and technical-check grounding.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


PILLARS = {"Conversion", "AOV", "Retention", "Acquisition", "Performance"}
REASON_SCHEMAS = {
    "experiments": "experiments.schema.json",
    "store_profile": "store_profile.schema.json",
    "visual_findings": "visual_findings.schema.json",
    "leaks": "leaks.schema.json",
    "competitors": "competitors.schema.json",
    "tech_checks": "tech_checks.schema.json",
    "synthesis": "synthesis.schema.json",
}
CONFIDENCE_BANDS = {
    "direct structural absence": (80, 88),
    "strong inference": (70, 80),
    "pattern / best-practice": (65, 72),
}


@dataclass(frozen=True)
class ValidationError:
    path: str
    code: str
    message: str
    category: str = "contract"


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: list[ValidationError]

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "errors": [asdict(error) for error in self.errors]}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def default_schema_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "schemas"


def validate_audit(store_root: str | Path, schema_dir: str | Path | None = None) -> ValidationResult:
    root = Path(store_root)
    schemas = Path(schema_dir) if schema_dir else default_schema_dir()
    errors: list[ValidationError] = []

    manifest = _load_required_json(root / "manifest.json", "manifest", errors)
    if manifest is None:
        return ValidationResult(False, errors)
    _validate_schema(manifest, load_json(schemas / "manifest.schema.json"), "manifest", errors)

    pages = _load_pages(root, manifest, schemas, errors)
    reason = _load_reason_files(root, schemas, errors)
    if not _has_reason(reason):
        return ValidationResult(False, errors)

    visual_ids = {finding.get("id") for finding in reason["visual_findings"].get("findings", [])}
    profile_tokens = _profile_tokens(reason["store_profile"])

    _validate_experiment_contract(root, reason["experiments"].get("experiments", []), pages, visual_ids, profile_tokens, errors)
    _validate_competitor_contract(reason["competitors"].get("competitors", []), errors)
    _validate_tech_contract(reason["tech_checks"].get("checks", []), pages, errors)

    return ValidationResult(ok=not errors, errors=errors)


def _load_required_json(path: Path, object_path: str, errors: list[ValidationError]) -> Any | None:
    if not path.exists():
        errors.append(ValidationError(object_path, "missing_file", f"Required file not found: {path}"))
        return None
    try:
        return load_json(path)
    except json.JSONDecodeError as exc:
        errors.append(ValidationError(object_path, "invalid_json", f"Invalid JSON in {path}: {exc}"))
        return None


def _load_pages(root: Path, manifest: dict[str, Any], schema_dir: Path, errors: list[ValidationError]) -> dict[str, dict[str, Any]]:
    pages: dict[str, dict[str, Any]] = {}
    page_schema = load_json(schema_dir / "page.schema.json")
    for idx, surface in enumerate(manifest.get("surfaces", [])):
        surface_id = surface.get("id")
        object_path = f"manifest.surfaces[{idx}].page_json"
        page_rel = surface.get("page_json")
        if not surface_id or not page_rel:
            continue
        page = _load_required_json(root / page_rel, object_path, errors)
        if page is None:
            continue
        _validate_schema(page, page_schema, surface_id, errors)
        pages[surface_id] = page
    return pages


def _load_reason_files(root: Path, schema_dir: Path, errors: list[ValidationError]) -> dict[str, Any]:
    reason: dict[str, Any] = {}
    for name, schema_name in REASON_SCHEMAS.items():
        object_path = f"reason.{name}"
        data = _load_required_json(root / "reason" / f"{name}.json", object_path, errors)
        if data is None:
            continue
        _validate_schema(data, load_json(schema_dir / schema_name), object_path, errors)
        reason[name] = data
    return reason


def _has_reason(reason: dict[str, Any]) -> bool:
    return all(name in reason for name in REASON_SCHEMAS)


def _validate_schema(instance: Any, schema: dict[str, Any], path: str, errors: list[ValidationError]) -> None:
    _validate_node(instance, schema, path, errors, schema)


def _validate_node(instance: Any, schema: dict[str, Any], path: str, errors: list[ValidationError], root_schema: dict[str, Any]) -> None:
    if "$ref" in schema:
        ref = schema["$ref"]
        if ref.startswith("#/$defs/"):
            schema = root_schema.get("$defs", {}).get(ref.rsplit("/", 1)[-1], {})

    expected = schema.get("type")
    if expected and not _matches_type(instance, expected):
        errors.append(ValidationError(path, "schema_type", f"Expected {expected}, got {type(instance).__name__}", "schema"))
        return

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(ValidationError(path, "schema_enum", f"Value {instance!r} not in enum {schema['enum']}", "schema"))

    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(ValidationError(path, "schema_min_length", "String is shorter than minLength", "schema"))
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(ValidationError(path, "schema_pattern", f"String does not match {schema['pattern']}", "schema"))

    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            errors.append(ValidationError(path, "schema_min_items", "Array has too few items", "schema"))
        item_schema = schema.get("items")
        if item_schema:
            for idx, item in enumerate(instance):
                _validate_node(item, item_schema, f"{path}[{idx}]", errors, root_schema)

    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(ValidationError(f"{path}.{key}", "schema_required", f"Missing required field {key}", "schema"))
        properties = schema.get("properties", {})
        for key, value in instance.items():
            if key in properties:
                _validate_node(value, properties[key], f"{path}.{key}", errors, root_schema)
            elif isinstance(schema.get("additionalProperties"), dict):
                _validate_node(value, schema["additionalProperties"], f"{path}.{key}", errors, root_schema)


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return (isinstance(value, int | float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    return True


def _validate_experiment_contract(
    root: Path,
    experiments: list[dict[str, Any]],
    pages: dict[str, dict[str, Any]],
    visual_ids: set[str],
    profile_tokens: set[str],
    errors: list[ValidationError],
) -> None:
    if len(experiments) != 10:
        errors.append(ValidationError("experiments", "experiment_count", f"{len(experiments)} experiments found; expected exactly 10"))

    missing = PILLARS - {exp.get("pillar") for exp in experiments}
    if missing:
        errors.append(ValidationError("experiments[*].pillar", "pillar_coverage", f"Missing pillars: {', '.join(sorted(missing))}"))

    for idx, exp in enumerate(experiments):
        evidence = exp.get("evidence", {})
        screenshot = evidence.get("screenshot", "")
        if screenshot and not (root / screenshot).exists():
            errors.append(ValidationError(f"experiments[{idx}].evidence.screenshot", "missing_screenshot", f"Screenshot does not exist: {screenshot}", "evidence"))

        signal = evidence.get("triggering_signal", "")
        signal_type = evidence.get("signal_type", "")
        if signal and not resolve_signal(signal, signal_type, pages, visual_ids):
            errors.append(ValidationError(f"experiments[{idx}].evidence.triggering_signal", "unresolved_signal", f"Signal does not resolve: {signal}", "evidence"))

        profile_ref = evidence.get("store_profile_ref", "")
        if profile_ref and not ref_overlaps_profile(profile_ref, profile_tokens):
            errors.append(ValidationError(f"experiments[{idx}].evidence.store_profile_ref", "specificity_overlap", f"No store_profile overlap for {profile_ref}", "specificity"))

        basis = exp.get("confidence_basis")
        confidence = exp.get("confidence")
        if isinstance(confidence, int):
            low, high = CONFIDENCE_BANDS.get(basis, (0, 100))
            if not (low <= confidence <= high):
                errors.append(ValidationError(f"experiments[{idx}].confidence", "confidence_band", f"{confidence} outside {low}-{high} for {basis}", "confidence"))


def _validate_competitor_contract(competitors: list[dict[str, Any]], errors: list[ValidationError]) -> None:
    if not 3 <= len(competitors) <= 4:
        errors.append(ValidationError("competitors", "competitor_count", f"{len(competitors)} competitors found; expected 3-4"))


def _validate_tech_contract(checks: list[dict[str, Any]], pages: dict[str, dict[str, Any]], errors: list[ValidationError]) -> None:
    if not 13 <= len(checks) <= 17:
        errors.append(ValidationError("tech_checks", "tech_check_count", f"{len(checks)} tech checks found; expected about 15"))
    for idx, check in enumerate(checks):
        status = check.get("status")
        grounded_in = check.get("grounded_in", "")
        if status in {"Pass", "Fail"} and not resolve_grounding(grounded_in, pages):
            errors.append(ValidationError(f"tech_checks[{idx}].grounded_in", "unresolved_grounding", f"{status} without resolvable grounded_in: {grounded_in}", "technical_truthfulness"))


def _profile_tokens(profile: dict[str, Any]) -> set[str]:
    tokens: set[str] = set()
    if profile.get("niche"):
        tokens.add(profile["niche"])
    for family in profile.get("families", []):
        if family.get("name"):
            tokens.add(family["name"])
        tokens.update(family.get("products", []))
    for key in ("jobs_to_be_done", "segments", "proof_points", "content_themes"):
        tokens.update(profile.get(key, []))
    return {_norm(token) for token in tokens if token}


def ref_overlaps_profile(ref: str, profile_tokens: set[str]) -> bool:
    for part in re.split(r"[;,]", ref):
        value = part.split(":", 1)[-1].strip()
        normalized = _norm(value)
        if normalized and any(normalized in token or token in normalized for token in profile_tokens):
            return True
    return False


def resolve_signal(signal: str, signal_type: str, pages: dict[str, dict[str, Any]], visual_ids: set[str]) -> bool:
    if signal_type == "visual":
        return signal.startswith("visual_findings.") and signal.split(".", 1)[1] in visual_ids
    if signal_type == "network":
        if ".network.responses[].status=" not in signal:
            return False
        surface_id = signal.split(".", 1)[0]
        try:
            wanted = int(signal.rsplit("=", 1)[1])
        except ValueError:
            return False
        return any(response.get("status") == wanted for response in pages.get(surface_id, {}).get("network", {}).get("responses", []))
    if signal_type == "cro_signals":
        if ".cro_signals." not in signal or ".present=" not in signal:
            return False
        surface_id = signal.split(".", 1)[0]
        key = signal.split(".cro_signals.", 1)[1].split(".", 1)[0]
        wanted = signal.rsplit("=", 1)[1].strip().lower()
        if wanted not in {"true", "false"}:
            return False
        node = pages.get(surface_id, {}).get("cro_signals", {}).get(key)
        return isinstance(node, dict) and node.get("present") is (wanted == "true")
    return False


def resolve_grounding(grounded_in: str, pages: dict[str, dict[str, Any]]) -> bool:
    text = grounded_in.strip()
    if not text or text.lower() == "not inspected":
        return False
    if ".network.responses[].status=" in text:
        return resolve_signal(text, "network", pages, set())

    clean = text.split(" ", 1)[0]
    parts = clean.split(".")
    if len(parts) < 2:
        return False
    surface_id, path_parts = parts[0], parts[1:]
    current: Any = pages.get(surface_id)
    for part in path_parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return False
    return current is not None


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Qosmic audit artifact contract.")
    parser.add_argument("store_root", help="Store artifact root, e.g. fixtures/sample_store")
    parser.add_argument("--schema-dir", default=None, help="Optional schema directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    args = parser.parse_args(argv)

    result = validate_audit(args.store_root, args.schema_dir)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print("VALID" if result.ok else "INVALID")
        for error in result.errors:
            print(f"- {error.path}: {error.message}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
