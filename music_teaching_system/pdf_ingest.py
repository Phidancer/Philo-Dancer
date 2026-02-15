from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExtractedPage:
    page: int
    text: str


@dataclass
class ParsedPDF:
    title: str
    pages: list[ExtractedPage]


KEYWORDS_SCORE = {"sheet", "staff", "measure", "谱", "五线谱", "音符"}
KEYWORDS_ANALYSIS = {"analysis", "chart", "diagram", "form", "harmony", "分析", "图表", "schenker"}


def _parse_with_pymupdf(path: Path) -> ParsedPDF:
    import fitz  # type: ignore

    doc = fitz.open(path)
    pages = [ExtractedPage(page=i + 1, text=doc[i].get_text("text")) for i in range(len(doc))]
    return ParsedPDF(title=path.stem, pages=pages)


def _parse_with_pypdf(path: Path) -> ParsedPDF:
    from pypdf import PdfReader  # type: ignore

    reader = PdfReader(str(path))
    pages = []
    for idx, page in enumerate(reader.pages, start=1):
        pages.append(ExtractedPage(page=idx, text=page.extract_text() or ""))
    return ParsedPDF(title=path.stem, pages=pages)


def parse_pdf(pdf_path: str | Path) -> ParsedPDF:
    """Extract text from PDF.

    Priority:
    1) PyMuPDF (fitz)
    2) pypdf
    3) UTF-8 text fallback split by form-feed
    """

    path = Path(pdf_path)

    for parser in (_parse_with_pymupdf, _parse_with_pypdf):
        try:
            return parser(path)
        except Exception:
            continue

    raw = path.read_text(encoding="utf-8", errors="ignore")
    segments = [s.strip() for s in raw.split("\f") if s.strip()] or [raw]
    pages = [ExtractedPage(page=i + 1, text=text) for i, text in enumerate(segments)]
    return ParsedPDF(title=path.stem, pages=pages)


def classify_page(text: str) -> str:
    lower = text.lower()
    score_hits = sum(1 for k in KEYWORDS_SCORE if k in lower)
    analysis_hits = sum(1 for k in KEYWORDS_ANALYSIS if k in lower)
    if score_hits and analysis_hits:
        return "hybrid"
    if score_hits:
        return "sheetmusic"
    if analysis_hits:
        return "analysis"
    return "context"
