from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    import adaptive_ui_service.app.services.retrieval_service as retrieval_service
    from adaptive_ui_service.app.core.config import settings
    from adaptive_ui_service.app.models.capability import MANIFEST_PATH, load_manifest

    parser = argparse.ArgumentParser(
        description="Build the persisted capability retrieval index"
    )
    parser.add_argument("--model", default=settings.embedding_model_name)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--out-dir", type=Path, default=settings.index_dir)
    arguments = parser.parse_args(argv)

    capabilities = load_manifest(arguments.manifest)
    embedder = retrieval_service.SentenceTransformerEmbedder(arguments.model)
    index, vectors, metadata = retrieval_service.build_index(
        capabilities,
        embedder,
        arguments.model,
        manifest_path=arguments.manifest,
    )
    retrieval_service.save_index(arguments.out_dir, index, vectors, metadata)

    print(
        f"Built {metadata.count} vectors (dimension {metadata.dimension}) "
        f"with {metadata.model_name} at {arguments.out_dir.resolve()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
