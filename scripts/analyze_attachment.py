from pathlib import Path

from docx import Document
from pypdf import PdfReader

from common import emit, log_action


def read_text(path: Path) -> tuple[str, str]:
    ext = path.suffix.lower()
    if ext in {".txt", ".md", ".csv", ".json", ".log"}:
        return path.read_text(errors="ignore"), "plain"
    if ext == ".pdf":
        reader = PdfReader(str(path))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
        return text, "pdf"
    if ext == ".docx":
        doc = Document(str(path))
        text = "\n".join(p.text for p in doc.paragraphs)
        return text, "docx"
    return "", "binary"


def summarize(text: str, max_chars: int = 1200) -> str:
    clean = " ".join(text.split())
    return clean[:max_chars]


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Analyze local attachment")
    p.add_argument("path")
    args = p.parse_args()

    path = Path(args.path)
    log_action("analyze_attachment.start", path=str(path))
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    text, mode = read_text(path)
    log_action("analyze_attachment.done", path=str(path), mode=mode, chars_extracted=len(text))
    emit(
        {
            "path": str(path.resolve()),
            "mode": mode,
            "size": path.stat().st_size,
            "chars_extracted": len(text),
            "summary": summarize(text) if text else None,
        }
    )


if __name__ == "__main__":
    main()
