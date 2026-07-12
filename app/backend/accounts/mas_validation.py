"""Server-side MAS validation (JSON Schema Draft 2020-12).

Every MAS document stored by the accounts feature is validated against the MAS
schemas on write — invalid documents are rejected with the exact validation
error, never stored or silently fixed.

The schema directory comes from OM_MAS_SCHEMA_DIR, defaulting to the MAS repo
checked out next to WebBackend (../MAS/schemas). All schema files register by
their declared $id (https://psma.com/mas/...), which mirrors the file layout,
so relative $refs resolve through the registry.
"""
import functools
import json
import os
import pathlib
import re

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


def _schema_dir() -> pathlib.Path:
    configured = os.getenv("OM_MAS_SCHEMA_DIR")
    path = pathlib.Path(configured) if configured else (_REPO_ROOT.parent / "MAS" / "schemas")
    if not path.is_dir():
        raise RuntimeError(
            f"MAS schema directory not found at {path}. Check out the MAS repo next to WebBackend "
            f"or set OM_MAS_SCHEMA_DIR.")
    return path


def _peas_schema_dir() -> pathlib.Path:
    """MAS schemas $ref PEAS (the one allowed cross-package dependency), so the
    registry needs the PEAS schemas too. Search order: OM_PEAS_SCHEMA_DIR, a
    PEAS checkout next to MAS, the canonical ~/PSMA/PEAS checkout."""
    candidates = []
    configured = os.getenv("OM_PEAS_SCHEMA_DIR")
    if configured:
        candidates.append(pathlib.Path(configured))
    candidates.append(_schema_dir().parent.parent / "PEAS" / "schemas")
    candidates.append(pathlib.Path.home() / "PSMA" / "PEAS" / "schemas")
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    raise RuntimeError(
        f"PEAS schema directory not found (tried {[str(c) for c in candidates]}). "
        f"Check out the PEAS repo or set OM_PEAS_SCHEMA_DIR.")


@functools.lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    schema_dir = _schema_dir()
    resources = []
    root_schema = None
    for directory in (schema_dir, _peas_schema_dir()):
        for file in directory.rglob("*.json"):
            with open(file) as f:
                schema = json.load(f)
            schema_id = schema.get("$id")
            if not schema_id:
                raise RuntimeError(f"Schema {file} has no $id — cannot build the reference registry")
            resources.append((schema_id, Resource.from_contents(schema)))
            if directory == schema_dir and file.parent == schema_dir and file.name == "MAS.json":
                root_schema = schema
    if root_schema is None:
        raise RuntimeError(f"MAS.json not found in {schema_dir}")
    registry = Registry().with_resources(resources)
    return Draft202012Validator(root_schema, registry=registry)


@functools.lru_cache(maxsize=1)
def mas_spec_version() -> str:
    """The released MAS version these schemas belong to, from MAS/CHANGELOG.md."""
    changelog = _schema_dir().parent / "CHANGELOG.md"
    if not changelog.is_file():
        raise RuntimeError(f"MAS CHANGELOG.md not found at {changelog} — cannot stamp mas_version")
    for line in changelog.read_text().splitlines():
        match = re.match(r"^## \[(\d+\.\d+\.\d+)\]", line)
        if match:
            return match.group(1)
    raise RuntimeError(f"No released version heading found in {changelog}")


def validate_mas(document) -> list[str]:
    """Return a list of human-readable validation errors (empty = valid)."""
    errors = []
    for error in sorted(_validator().iter_errors(document), key=lambda e: list(e.absolute_path)):
        location = "/".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"{location}: {error.message}")
        if len(errors) >= 20:
            errors.append("... further errors truncated")
            break
    return errors
