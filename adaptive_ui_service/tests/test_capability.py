import json

import pytest
from pydantic import ValidationError

from adaptive_ui_service.app.models.capability import Capability, load_manifest


def test_manifest_loads_successfully() -> None:
    capabilities = load_manifest()

    assert len(capabilities) >= 20
    assert all(isinstance(capability, Capability) for capability in capabilities)


def test_missing_field_fails_validation() -> None:
    with pytest.raises(ValidationError):
        Capability.model_validate(
            {
                "capability_id": "test_capability",
                "name": "Test capability",
                "category": "view_toggles",
                "required_permissions": [],
                "ui_change": {},
            }
        )


def test_duplicate_ids_fail_validation(tmp_path) -> None:
    entry = {
        "capability_id": "duplicate_capability",
        "name": "Duplicate capability",
        "description": "A test capability.",
        "category": "view_toggles",
        "required_permissions": [],
        "ui_change": {},
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps([entry, entry]), encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate_capability"):
        load_manifest(manifest_path)


def test_ids_are_unique() -> None:
    capabilities = load_manifest()
    ids = [capability.capability_id for capability in capabilities]

    assert len(ids) == len(set(ids))
