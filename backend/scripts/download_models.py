"""Pre-fetches Hugging Face model weights into the image's HF cache at build
time, so the running container never needs network access to Hugging Face.
Run this as its own Docker layer, before COPYing application code, so app
changes don't invalidate the (large) model download cache.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from transformers import (  # noqa: E402
    AutoModelForCausalLM,
    AutoModelForSeq2SeqLM,
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

from app.config import get_settings  # noqa: E402


def main() -> None:
    settings = get_settings()

    print(f"Descargando LM español: {settings.spanish_lm_model}")
    AutoTokenizer.from_pretrained(settings.spanish_lm_model)
    AutoModelForCausalLM.from_pretrained(settings.spanish_lm_model)

    if settings.enable_translation_classifier:
        print(f"Descargando traductor: {settings.translation_model}")
        AutoTokenizer.from_pretrained(settings.translation_model)
        AutoModelForSeq2SeqLM.from_pretrained(settings.translation_model)

        print(f"Descargando clasificador inglés: {settings.english_classifier_model}")
        AutoTokenizer.from_pretrained(settings.english_classifier_model)
        AutoModelForSequenceClassification.from_pretrained(settings.english_classifier_model)

    print("Descarga de modelos completa.")


if __name__ == "__main__":
    main()
