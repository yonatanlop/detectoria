"""Source D (optional, feature-flagged): ES->EN translation + English AI-text classifier.

This is the weakest and most indirect signal in the ensemble (translation adds
noise, and the classifier was trained on GPT-2-era text, not modern LLMs), so
it is disabled by default and given the lowest aggregation weight when enabled.
"""

import torch

from . import DetectorOutput

_MAX_SPANISH_TOKENS = 1024  # bounds translation + classification compute cost


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


class TranslationClassifierDetector:
    def __init__(self, translator_tokenizer, translator_model, classifier_tokenizer, classifier_model):
        self.translator_tokenizer = translator_tokenizer
        self.translator_model = translator_model
        self.classifier_tokenizer = classifier_tokenizer
        self.classifier_model = classifier_model

        self._fake_label_index = self._resolve_fake_label_index(classifier_model)

        translator_max_len = getattr(translator_model.config, "max_position_embeddings", 512)
        self.translator_chunk_size = min(translator_max_len - 2, 480)

        classifier_max_len = getattr(classifier_model.config, "max_position_embeddings", 512)
        self.classifier_chunk_size = min(classifier_max_len - 2, 480)

    @staticmethod
    def _resolve_fake_label_index(classifier_model) -> int:
        id2label = getattr(classifier_model.config, "id2label", {}) or {}
        for idx, label in id2label.items():
            if "fake" in str(label).lower():
                return int(idx)
        return 1  # conventional fallback: index 1 = "generated/fake"

    @torch.inference_mode()
    def _translate(self, text: str) -> str:
        input_ids = self.translator_tokenizer(text, add_special_tokens=False)["input_ids"]
        input_ids = input_ids[:_MAX_SPANISH_TOKENS]

        translated_parts = []
        for start in range(0, len(input_ids), self.translator_chunk_size):
            chunk = input_ids[start : start + self.translator_chunk_size]
            if not chunk:
                continue
            chunk_tensor = torch.tensor([chunk], dtype=torch.long)
            generated = self.translator_model.generate(chunk_tensor, max_new_tokens=512)
            translated_parts.append(
                self.translator_tokenizer.decode(generated[0], skip_special_tokens=True)
            )
        return " ".join(translated_parts)

    @torch.inference_mode()
    def _classify(self, english_text: str) -> float:
        input_ids = self.classifier_tokenizer(english_text, add_special_tokens=False)["input_ids"]
        if not input_ids:
            return 0.5

        weighted_fake_prob = 0.0
        total_tokens = 0
        for start in range(0, len(input_ids), self.classifier_chunk_size):
            chunk = input_ids[start : start + self.classifier_chunk_size]
            if not chunk:
                continue
            encoded = self.classifier_tokenizer.prepare_for_model(
                chunk, add_special_tokens=True, return_tensors="pt"
            )
            logits = self.classifier_model(**encoded).logits[0]
            probs = torch.softmax(logits, dim=-1)
            fake_prob = float(probs[self._fake_label_index].item())
            weighted_fake_prob += fake_prob * len(chunk)
            total_tokens += len(chunk)

        return weighted_fake_prob / total_tokens if total_tokens else 0.5

    def analyze(self, spanish_text: str) -> DetectorOutput:
        try:
            english_text = self._translate(spanish_text)
            if not english_text.strip():
                raise ValueError("Traducción vacía")
            score = self._classify(english_text)
            details = (
                "Texto traducido a inglés y evaluado con un clasificador entrenado para "
                "distinguir texto generado por GPT-2 vs. humano. Señal experimental y "
                "menos confiable por la doble indirección (traducción + modelo antiguo)."
            )
        except Exception as exc:  # pragma: no cover - defensive fallback for an optional source
            score = 0.5
            details = f"No se pudo completar esta fuente experimental ({exc}); se usó un valor neutral."

        return DetectorOutput(
            id="translation_classifier",
            name="Traducción EN + clasificador (experimental)",
            score=_clamp(score),
            details=details,
        )
