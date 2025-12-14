import argparse
import json
import re
import string
from collections import Counter
from pathlib import Path


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def remove_punctuation(text: str) -> str:
    translator = str.maketrans("", "", string.punctuation)
    return text.translate(translator)


def token_counts(text: str) -> Counter[str]:
    tokens = re.findall(r"\b\w+\b", text.lower())
    return Counter(tokens)


def main() -> None:
    parser = argparse.ArgumentParser(description="Refine a raw text file.")
    parser.add_argument("source", type=Path, help="Path to a raw .txt file in data/raw.")
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    raw_dir = Path(__file__).resolve().parent.parent / "data" / "raw"

    if not source.exists():
        parser.error(f"File not found: {source}")
    if source.suffix.lower() != ".txt":
        parser.error("Provide a .txt file from data/raw.")
    if raw_dir not in source.parents:
        parser.error(f"Source must be inside {raw_dir}")

    text = source.read_text(encoding="utf-8")

    refined_dir = raw_dir.parent / "refined"
    refined_dir.mkdir(parents=True, exist_ok=True)

    normalized_text = normalize_whitespace(text)
    punctuation_removed_text = remove_punctuation(text)
    lowercased_text = text.lower()
    counts = token_counts(text)

    normalized_path = refined_dir / f"{source.stem}.normalized.txt"
    punctuation_removed_path = refined_dir / f"{source.stem}.nopunct.txt"
    lowercased_path = refined_dir / f"{source.stem}.lower.txt"
    counts_path = refined_dir / f"{source.stem}.counts.json"

    normalized_path.write_text(normalized_text, encoding="utf-8")
    punctuation_removed_path.write_text(punctuation_removed_text, encoding="utf-8")
    lowercased_path.write_text(lowercased_text, encoding="utf-8")
    with counts_path.open("w", encoding="utf-8") as f:
        json.dump(counts, f, indent=2)

    print(normalized_path)
    print(punctuation_removed_path)
    print(lowercased_path)
    print(counts_path)


if __name__ == "__main__":
    main()
