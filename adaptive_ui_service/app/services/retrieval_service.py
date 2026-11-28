from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Protocol

import faiss
import numpy as np
from pydantic import BaseModel, ValidationError

from adaptive_ui_service.app.core.exceptions import IndexNotFoundError, IndexStaleError
from adaptive_ui_service.app.models.capability import MANIFEST_PATH, Capability
from adaptive_ui_service.app.models.retrieval import ScoredCapability


class Embedder(Protocol):
    def encode(self, texts: list[str]) -> np.ndarray: ...


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> np.ndarray:
        return np.asarray(
            self._model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False,
            ),
            dtype=np.float32,
        )


class IndexMeta(BaseModel):
    schema_version: int
    model_name: str
    dimension: int
    count: int
    capability_ids: list[str]
    manifest_sha256: str


def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    normalized_input = np.asarray(vectors, dtype=np.float32)
    if normalized_input.ndim != 2:
        raise ValueError("Embeddings must be a two-dimensional array")
    if not np.isfinite(normalized_input).all():
        raise ValueError("Embeddings must contain only finite values")

    norms = np.linalg.norm(normalized_input, axis=1, keepdims=True)
    return normalized_input / np.maximum(norms, 1e-12)


def _manifest_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_index(
    capabilities: list[Capability],
    embedder: Embedder,
    model_name: str,
    manifest_path: Path = MANIFEST_PATH,
) -> tuple[faiss.Index, np.ndarray, IndexMeta]:
    if not capabilities:
        raise ValueError("Cannot build a retrieval index from an empty manifest")

    raw_vectors = np.asarray(
        embedder.encode([capability.description for capability in capabilities]),
        dtype=np.float32,
    )
    if raw_vectors.ndim != 2 or raw_vectors.shape[0] != len(capabilities):
        raise ValueError("Embedder must return one vector for each description")
    if raw_vectors.shape[1] == 0:
        raise ValueError("Embedding vectors must have at least one dimension")

    vectors = l2_normalize(raw_vectors)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    metadata = IndexMeta(
        schema_version=1,
        model_name=model_name,
        dimension=vectors.shape[1],
        count=len(capabilities),
        capability_ids=[capability.capability_id for capability in capabilities],
        manifest_sha256=_manifest_hash(manifest_path),
    )
    return index, vectors, metadata


def save_index(
    index_dir: Path,
    index: faiss.Index,
    vectors: np.ndarray,
    metadata: IndexMeta,
) -> None:
    vectors = np.asarray(vectors, dtype=np.float32)
    if vectors.shape != (metadata.count, metadata.dimension):
        raise ValueError("Vector shape does not match index metadata")
    if index.ntotal != metadata.count or index.d != metadata.dimension:
        raise ValueError("FAISS index dimensions do not match index metadata")

    index_dir = index_dir.resolve()
    index_dir.parent.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(dir=index_dir.parent) as temp_path:
        temp_dir = Path(temp_path)
        faiss.write_index(index, str(temp_dir / "capabilities.faiss"))
        np.save(temp_dir / "vectors.npy", vectors, allow_pickle=False)
        (temp_dir / "meta.json").write_text(
            metadata.model_dump_json(indent=2),
            encoding="utf-8",
        )

        (index_dir / "meta.json").unlink(missing_ok=True)
        for filename in ("capabilities.faiss", "vectors.npy", "meta.json"):
            os.replace(temp_dir / filename, index_dir / filename)


def load_index(index_dir: Path) -> tuple[faiss.Index, np.ndarray, IndexMeta]:
    index_dir = index_dir.resolve()
    meta_path = index_dir / "meta.json"
    if not meta_path.exists():
        raise IndexNotFoundError(f"Retrieval index metadata not found in {index_dir}")

    artifact_paths = (
        index_dir / "capabilities.faiss",
        index_dir / "vectors.npy",
    )
    missing_paths = [path.name for path in artifact_paths if not path.is_file()]
    if missing_paths:
        raise IndexStaleError(
            f"Retrieval index artifacts are incomplete: {', '.join(missing_paths)}"
        )

    try:
        metadata = IndexMeta.model_validate_json(meta_path.read_text(encoding="utf-8"))
    except ValidationError as error:
        raise IndexStaleError("Retrieval index metadata is invalid") from error
    if metadata.schema_version != 1:
        raise IndexStaleError(
            f"Unsupported retrieval index schema version: {metadata.schema_version}"
        )

    index = faiss.read_index(str(artifact_paths[0]))
    vectors = np.load(artifact_paths[1], allow_pickle=False)
    if (
        index.metric_type != faiss.METRIC_INNER_PRODUCT
        or index.d != metadata.dimension
        or index.ntotal != metadata.count
        or vectors.shape != (metadata.count, metadata.dimension)
    ):
        raise IndexStaleError("Retrieval index artifacts do not match their metadata")

    return index, vectors, metadata


class RetrievalService:
    def __init__(
        self,
        index: faiss.Index,
        ordered_capabilities: list[Capability],
        embedder: Embedder | None,
    ) -> None:
        if index.ntotal != len(ordered_capabilities):
            raise ValueError("Index entries and capabilities must have matching counts")
        self._index = index
        self._capabilities = ordered_capabilities
        self._embedder = embedder

    @classmethod
    def empty(cls) -> RetrievalService:
        return cls(faiss.IndexFlatIP(1), [], None)

    @classmethod
    def from_artifacts(
        cls,
        index_dir: Path,
        capabilities: list[Capability],
        *,
        model_name: str,
        manifest_path: Path = MANIFEST_PATH,
        embedder: Embedder | None = None,
    ) -> RetrievalService:
        index, _vectors, metadata = load_index(index_dir)
        expected_ids = [capability.capability_id for capability in capabilities]

        if metadata.model_name != model_name:
            raise IndexStaleError(
                f"Index model {metadata.model_name!r} does not match "
                f"configured model {model_name!r}"
            )
        if metadata.manifest_sha256 != _manifest_hash(manifest_path):
            raise IndexStaleError("Index was built from a different manifest")
        if metadata.capability_ids != expected_ids:
            raise IndexStaleError("Index capability order does not match the manifest")

        return cls(
            index=index,
            ordered_capabilities=capabilities,
            embedder=(
                embedder
                if embedder is not None
                else SentenceTransformerEmbedder(model_name)
            ),
        )

    def retrieve(self, query: str, k: int = 5) -> list[ScoredCapability]:
        if k < 1:
            raise ValueError("k must be at least 1")
        if not query.strip() or self._index.ntotal == 0:
            return []
        if self._embedder is None:
            raise RuntimeError("An embedder is required for a non-empty index")

        query_vectors = l2_normalize(self._embedder.encode([query]))
        if query_vectors.shape[0] != 1 or query_vectors.shape[1] != self._index.d:
            raise ValueError("Query embedding dimensions do not match the index")

        scores, indices = self._index.search(
            query_vectors,
            min(k, self._index.ntotal),
        )
        return [
            ScoredCapability(
                capability=self._capabilities[int(index)],
                score=float(score),
            )
            for score, index in zip(scores[0], indices[0], strict=True)
            if index >= 0
        ]
