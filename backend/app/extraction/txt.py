from charset_normalizer import from_bytes

from . import ExtractionError


def extract_txt(data: bytes) -> str:
    result = from_bytes(data).best()
    if result is None:
        raise ExtractionError("No se pudo determinar la codificación del archivo de texto.")
    return str(result)
