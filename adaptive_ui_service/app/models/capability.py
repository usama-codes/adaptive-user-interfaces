from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, field_validator

MANIFEST_PATH = Path(__file__).parents[2] / "data" / "capability_manifest.json"


class Capability(BaseModel):
    capability_id: str
    name: str
    description: str
    category: str
    required_permissions: list[str]
    ui_change: dict[str, Any]

    @field_validator("capability_id")
    @classmethod
    def id_must_be_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("capability_id must not be empty")
        return value


def load_manifest(path: Path = MANIFEST_PATH) -> list[Capability]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    capabilities = [Capability.model_validate(entry) for entry in raw]
    _assert_unique_ids(capabilities)
    return capabilities


def _assert_unique_ids(capabilities: list[Capability]) -> None:
    seen: set[str] = set()
    for capability in capabilities:
        if capability.capability_id in seen:
            raise ValueError(f"Duplicate capability_id: {capability.capability_id!r}")
        seen.add(capability.capability_id)
