"""Generate embeddings for all restaurants."""

from pathlib import Path

import faiss
import numpy as np

from vibecheck.embeddings.generator import EmbeddingGenerator


def main():
    """Generate and save embeddings."""
    print("Generating embeddings...")
    generator = EmbeddingGenerator()
    embeddings, meta_ids = generator.generate_all()

    # Save embeddings
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    np.save(output_dir / "vibe_embeddings.npy", embeddings)
    np.save(output_dir / "meta_ids.npy", np.array(meta_ids))

    # Create FAISS index
    print("Building FAISS index...")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    faiss.write_index(index, str(output_dir / "vibecheck_index.faiss"))

    print(f"✅ Saved {len(meta_ids)} embeddings to {output_dir}")


if __name__ == "__main__":
    main()
