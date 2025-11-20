"""Create vibe map visualization."""

from pathlib import Path

from vibecheck.analysis.vibe_mapper import VibeMapper


def main():
    """Generate and save vibe map."""
    mapper = VibeMapper()
    df = mapper.create_map()

    output_path = Path("data/processed/vibe_map.csv")
    df.to_csv(output_path, index=False)

    print(f"✅ Vibe map saved to {output_path}")
    print(f"   Total restaurants: {len(df)}")
    print(f"   Clusters found: {df['cluster'].nunique()}")


if __name__ == "__main__":
    main()
