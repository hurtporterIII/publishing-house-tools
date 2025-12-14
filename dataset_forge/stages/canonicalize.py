import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

REQUIRED_FIELDS = {"chunk_id", "title", "summary", "keywords", "confidence"}


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc
            validate_record(record, line_number)
            records.append(record)
    return records


def validate_record(record: Dict[str, Any], line_number: int) -> None:
    missing = REQUIRED_FIELDS - record.keys()
    if missing:
        raise ValueError(f"Missing fields {sorted(missing)} on line {line_number}")
    if not isinstance(record.get("keywords"), list):
        raise ValueError(f"'keywords' must be a list on line {line_number}")


def prompt_edit(record: Dict[str, Any]) -> Dict[str, Any]:
    print("\n---- Draft ----")
    print(f"chunk_id : {record.get('chunk_id', '')}")
    print(f"title    : {record.get('title', '')}")
    print(f"summary  : {record.get('summary', '')}")
    print(f"keywords : {record.get('keywords', [])}")
    print(f"confidence: {record.get('confidence', 0)}")

    def prompt_field(label: str, current: str) -> str:
        response = input(f"{label} [{current}]: ").strip()
        return response if response else current

    title = prompt_field("Title", record.get("title", ""))
    summary = prompt_field("Summary", record.get("summary", ""))

    keywords_current = ", ".join(record.get("keywords", []))
    keywords_input = input(f"Keywords (comma separated) [{keywords_current}]: ").strip()
    keywords = (
        [kw.strip() for kw in keywords_input.split(",") if kw.strip()]
        if keywords_input
        else record.get("keywords", [])
    )

    approve_input = input("Approve? (y/N): ").strip().lower()
    approved = approve_input == "y"

    return {
        "chunk_id": record.get("chunk_id", ""),
        "title": title,
        "summary": summary,
        "keywords": keywords,
        "confidence": record.get("confidence", 0.0),
        "approved": approved,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Canonicalize semantic drafts.")
    parser.add_argument(
        "source", type=Path, help="Path to a drafts .jsonl file in data/drafts."
    )
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    drafts_dir = Path(__file__).resolve().parent.parent / "data" / "drafts"

    if not source.exists():
        parser.error(f"File not found: {source}")
    if source.suffix.lower() != ".jsonl":
        parser.error("Provide a .jsonl drafts file from data/drafts.")
    if drafts_dir not in source.parents:
        parser.error(f"Source must be inside {drafts_dir}")

    drafts = load_jsonl(source)

    canonical_dir = drafts_dir.parent / "canonical"
    canonical_dir.mkdir(parents=True, exist_ok=True)

    output_path = canonical_dir / f"{source.stem}.canonical.jsonl"

    canonical_records = [prompt_edit(record) for record in drafts]

    with output_path.open("w", encoding="utf-8") as f:
        for record in canonical_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(output_path)


if __name__ == "__main__":
    main()
