import argparse
import json
import re
from pathlib import Path


def split_chunks(text: str) -> list[str]:
    parts = re.split(r"\n{2,}", text)
    trimmed = [part.strip() for part in parts]
    return [part for part in trimmed if part]


def build_records(chunks: list[str]) -> list[dict[str, str]]:
    records = []
    for index, chunk in enumerate(chunks, start=1):
        records.append({"id": f"chunk-{index:04d}", "text": chunk})
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Segment normalized text into chunks.")
    parser.add_argument(
        "source", type=Path, help="Path to a normalized .txt file in data/refined."
    )
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    refined_dir = Path(__file__).resolve().parent.parent / "data" / "refined"

    if not source.exists():
        parser.error(f"File not found: {source}")
    if source.suffix.lower() != ".txt":
        parser.error("Provide a .txt file from data/refined.")
    if refined_dir not in source.parents:
        parser.error(f"Source must be inside {refined_dir}")

    text = source.read_text(encoding="utf-8")

    chunks = split_chunks(text)
    records = build_records(chunks)

    chunks_dir = refined_dir.parent / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    output_path = chunks_dir / f"{source.stem}.chunks.json"

    output_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(output_path)


if __name__ == "__main__":
    main()
