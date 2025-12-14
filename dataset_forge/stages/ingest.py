import argparse
from pathlib import Path
import zipfile
from xml.etree import ElementTree

try:
    from pypdf import PdfReader  # type: ignore
except ImportError:
    try:
        from PyPDF2 import PdfReader  # type: ignore
    except ImportError:
        PdfReader = None  # type: ignore


def extract_pdf_text(path: Path) -> str:
    if PdfReader is None:
        raise RuntimeError("PDF support requires pypdf or PyPDF2 to be installed.")

    reader = PdfReader(str(path))
    pieces = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            pieces.append(page_text)
    return "".join(pieces)


def extract_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        with archive.open("word/document.xml") as document_xml:
            tree = ElementTree.parse(document_xml)

    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    for para in tree.getroot().iterfind(".//w:p", namespaces=namespace):
        parts = []
        for node in para.iter():
            tag = node.tag
            if tag == f"{{{namespace['w']}}}t":
                parts.append(node.text or "")
            elif tag == f"{{{namespace['w']}}}tab":
                parts.append("\t")
            elif tag in {
                f"{{{namespace['w']}}}br",
                f"{{{namespace['w']}}}cr",
            }:
                parts.append("\n")
        paragraphs.append("".join(parts))
    return "\n".join(paragraphs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a PDF or DOCX into raw text.")
    parser.add_argument("source", type=Path, help="Path to the PDF or DOCX file.")
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    if not source.exists():
        parser.error(f"File not found: {source}")

    suffix = source.suffix.lower()
    if suffix == ".pdf":
        text = extract_pdf_text(source)
    elif suffix == ".docx":
        text = extract_docx_text(source)
    else:
        parser.error("Unsupported file type. Provide a PDF or DOCX file.")

    output_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{source.stem}.txt"

    output_path.write_text(text, encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
