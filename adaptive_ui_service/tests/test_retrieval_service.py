import json
import re
import zlib

import numpy as np
import pytest

import adaptive_ui_service.app.services.retrieval_service as retrieval_service
from adaptive_ui_service.app.core.exceptions import IndexStaleError
from adaptive_ui_service.app.models.capability import Capability


class HashEmbedder:
    def __init__(self, dimension: int = 64) -> None:
        self.dimension = dimension

    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), self.dimension), dtype=np.float32)
        for row, text in enumerate(texts):
            for token in re.findall(r"\w+", text.lower()):
                bucket = zlib.crc32(token.encode("utf-8")) % self.dimension
                vectors[row, bucket] += 1
        return vectors


@pytest.fixture
def capabilities() -> list[Capability]:
    return [
        Capability(
            capability_id="column_hide_assignee",
            name="Hide the Assignee column",
            description="Hide the Assignee column in the work-package list.",
            category="column_visibility",
            required_permissions=["view_work_packages"],
            ui_change={"action": "set_column_visibility", "target": "assignedTo"},
        ),
        Capability(
            capability_id="column_show_status",
            name="Show the Status column",
            description="Show the Status column in the work-package list.",
            category="column_visibility",
            required_permissions=["view_work_packages"],
            ui_change={"action": "set_column_visibility", "target": "status"},
        ),
        Capability(
            capability_id="view_switch_to_gantt",
            name="Show work packages as a Gantt chart",
            description="Display work packages in the Gantt representation.",
            category="view_toggles",
            required_permissions=["view_work_packages"],
            ui_change={"action": "select_view", "target": "work_packages"},
        ),
        Capability(
            capability_id="time_chart_group_by_month",
            name="Group the work-over-time chart by month",
            description="Display the work-over-time chart with monthly grouping.",
            category="time_charts",
            required_permissions=["view_work_packages"],
            ui_change={"action": "set_grouping", "target": "time_chart"},
        ),
        Capability(
            capability_id="widget_move_project_summary",
            name="Move the project summary widget",
            description="Move the project summary widget to another position.",
            category="widget_placement",
            required_permissions=["manage_dashboards"],
            ui_change={"action": "move_widget", "target": "project_summary"},
        ),
        Capability(
            capability_id="view_expand_all",
            name="Expand all work-package hierarchies",
            description="Expand all parent and child work-package rows.",
            category="view_toggles",
            required_permissions=["view_work_packages"],
            ui_change={"action": "expand_all", "target": "work_packages"},
        ),
    ]


def _write_manifest(path, capabilities: list[Capability]) -> None:
    path.write_text(
        json.dumps(
            [capability.model_dump(mode="json") for capability in capabilities],
            indent=2,
        ),
        encoding="utf-8",
    )


def test_known_query_returns_expected_capability_in_top_three(
    capabilities: list[Capability], tmp_path
) -> None:
    manifest_path = tmp_path / "manifest.json"
    _write_manifest(manifest_path, capabilities)
    index, _vectors, _metadata = retrieval_service.build_index(
        capabilities,
        HashEmbedder(),
        "test-model",
        manifest_path,
    )
    service = retrieval_service.RetrievalService(index, capabilities, HashEmbedder())

    results = service.retrieve("Please hide the Assignee column")

    assert "column_hide_assignee" in [
        result.capability.capability_id for result in results[:3]
    ]


def test_k_limits_results_and_rejects_non_positive_values(
    capabilities: list[Capability], tmp_path
) -> None:
    manifest_path = tmp_path / "manifest.json"
    _write_manifest(manifest_path, capabilities)
    index, _vectors, _metadata = retrieval_service.build_index(
        capabilities,
        HashEmbedder(),
        "test-model",
        manifest_path,
    )
    service = retrieval_service.RetrievalService(index, capabilities, HashEmbedder())

    assert len(service.retrieve("work-package view", k=2)) == 2
    assert len(service.retrieve("work-package view", k=100)) == len(capabilities)
    with pytest.raises(ValueError, match="k must be at least 1"):
        service.retrieve("work-package view", k=0)


def test_empty_index_returns_no_results() -> None:
    assert retrieval_service.RetrievalService.empty().retrieve("any query") == []


def test_normalization_handles_zero_vectors_without_nan() -> None:
    vectors = retrieval_service.l2_normalize(
        np.array([[0, 0], [3, 4]], dtype=np.float32)
    )

    assert np.isfinite(vectors).all()
    assert vectors[0].tolist() == [0.0, 0.0]
    assert np.linalg.norm(vectors[1]) == pytest.approx(1.0)


def test_artifact_round_trip_preserves_mapping_and_scores(
    capabilities: list[Capability], tmp_path
) -> None:
    manifest_path = tmp_path / "manifest.json"
    index_dir = tmp_path / "index"
    _write_manifest(manifest_path, capabilities)
    embedder = HashEmbedder()
    index, vectors, metadata = retrieval_service.build_index(
        capabilities,
        embedder,
        "test-model",
        manifest_path,
    )
    retrieval_service.save_index(index_dir, index, vectors, metadata)

    service = retrieval_service.RetrievalService.from_artifacts(
        index_dir,
        capabilities,
        model_name="test-model",
        manifest_path=manifest_path,
        embedder=embedder,
    )
    results = service.retrieve(capabilities[0].description)

    assert results[0].capability.capability_id == capabilities[0].capability_id
    assert results[0].score == pytest.approx(1.0, abs=1e-5)
    assert all(left.score >= right.score for left, right in zip(results, results[1:]))


def test_stale_model_name_is_rejected(capabilities: list[Capability], tmp_path) -> None:
    manifest_path = tmp_path / "manifest.json"
    index_dir = tmp_path / "index"
    _write_manifest(manifest_path, capabilities)
    index, vectors, metadata = retrieval_service.build_index(
        capabilities,
        HashEmbedder(),
        "built-model",
        manifest_path,
    )
    retrieval_service.save_index(index_dir, index, vectors, metadata)

    with pytest.raises(IndexStaleError, match="configured model"):
        retrieval_service.RetrievalService.from_artifacts(
            index_dir,
            capabilities,
            model_name="configured-model",
            manifest_path=manifest_path,
            embedder=HashEmbedder(),
        )


def test_stale_manifest_hash_is_rejected(
    capabilities: list[Capability], tmp_path
) -> None:
    manifest_path = tmp_path / "manifest.json"
    index_dir = tmp_path / "index"
    _write_manifest(manifest_path, capabilities)
    index, vectors, metadata = retrieval_service.build_index(
        capabilities,
        HashEmbedder(),
        "test-model",
        manifest_path,
    )
    retrieval_service.save_index(index_dir, index, vectors, metadata)
    manifest_path.write_text("[]", encoding="utf-8")

    with pytest.raises(IndexStaleError, match="different manifest"):
        retrieval_service.RetrievalService.from_artifacts(
            index_dir,
            capabilities,
            model_name="test-model",
            manifest_path=manifest_path,
            embedder=HashEmbedder(),
        )
