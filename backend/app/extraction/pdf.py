import io

import pdfplumber
from pypdf import PdfReader

from . import ExtractionError


def _extract_with_pdfplumber(data: bytes) -> str:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return "\n".join(pages).strip()


def _extract_with_pypdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def extract_pdf(data: bytes, min_chars: int) -> str:
    try:
        text = _extract_with_pdfplumber(data)
    except Exception:
        text = ""

    if len(text) < min_chars:
        try:
            fallback_text = _extract_with_pypdf(data)
        except Exception as exc:
            raise ExtractionError(f"No se pudo leer el PDF: {exc}") from exc
        if len(fallback_text) > len(text):
            text = fallback_text

    if len(text) < min_chars:
        raise ExtractionError(
            "No se pudo extraer suficiente texto del PDF. "
            "Puede ser un documento escaneado (imagen) sin capa de texto; "
            "el OCR no está soportado en esta versión."
        )
    return text
