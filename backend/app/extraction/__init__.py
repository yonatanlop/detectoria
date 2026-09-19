class ExtractionError(Exception):
    """Raised when text cannot be extracted from an uploaded document."""


class UnsupportedFileTypeError(ExtractionError):
    """Raised when the uploaded file extension is not supported."""


SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx"}


def extract_text(filename: str, data: bytes, min_chars: int) -> str:
    from .docx import extract_docx
    from .pdf import extract_pdf
    from .txt import extract_txt

    lower_name = filename.lower()
    if lower_name.endswith(".txt"):
        text = extract_txt(data)
    elif lower_name.endswith(".pdf"):
        text = extract_pdf(data, min_chars=min_chars)
    elif lower_name.endswith(".docx"):
        text = extract_docx(data)
    else:
        raise UnsupportedFileTypeError(
            f"Tipo de archivo no soportado. Formatos aceptados: {', '.join(sorted(SUPPORTED_EXTENSIONS))}."
        )

    if len(text.strip()) < min_chars:
        raise ExtractionError(
            f"El documento tiene muy poco texto extraíble (mínimo {min_chars} caracteres)."
        )
    return text
