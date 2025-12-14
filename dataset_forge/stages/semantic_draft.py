import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

try:
    from openai import OpenAI  # type: ignore
except ImportError:
    OpenAI = None  # type: ignore


SYSTEM_PROMPT = (
    "You are a careful extractor. Produce a single JSON object with fields:\n"
    '- "chunk_id": the provided chunk id\n'
    '- "title": short title or "" if unclear\n'
    '- "summary": brief summary or "" if unclear\n'
    '- "keywords": array of short keywords or [] if unclear\n'
    '- "confidence": always 0.0\n'
    "Do not add fields. Do not explain. Return JSON only."
)


def load_chunks(path: Path) -> List[Dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_client(api_key: str | None):
    if OpenAI is None:
        raise RuntimeError("openai package is required for this script.")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY to use this script.")
    return OpenAI(api_key=api_key)


def draft_semantic_entry(client: Any, model: str, chunk: Dict[str, Any]) -> Dict[str, Any]:
    chunk_id = chunk.get("id") or ""
    chunk_text = chunk.get("text") or ""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Chunk ID: {chunk_id}\n\nText:\n{chunk_text}",
        },
    ]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        data = {
            "chunk_id": chunk_id,
            "title": "",
            "summary": "",
            "keywords": [],
            "confidence": 0.0,
        }
    data["confidence"] = 0.0
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Draft semantic entries for chunks.")
    parser.add_argument(
        "source", type=Path, help="Path to a chunks .json file in data/chunks."
    )
    parser.add_argument(
        "--model", default="gpt-4o-mini", help="LLM model name for drafting."
    )
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    chunks_dir = Path(__file__).resolve().parent.parent / "data" / "chunks"

    if not source.exists():
        parser.error(f"File not found: {source}")
    if source.suffix.lower() != ".json":
        parser.error("Provide a .json chunks file from data/chunks.")
    if chunks_dir not in source.parents:
        parser.error(f"Source must be inside {chunks_dir}")

    chunks = load_chunks(source)

    client = ensure_client(api_key=os.getenv("OPENAI_API_KEY"))
    records = []
    for chunk in chunks:
        records.append(draft_semantic_entry(client, args.model, chunk))

    drafts_dir = chunks_dir.parent / "drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)

    base_name = source.stem.removesuffix(".chunks")
    output_path = drafts_dir / f"{base_name}.drafts.jsonl"

    with output_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(output_path)


if __name__ == "__main__":
    main()
