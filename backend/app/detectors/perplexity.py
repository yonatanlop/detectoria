"""Source B (perplexity/burstiness) and Source C (GLTR-style token-rank/entropy).

Both sources are derived from a single forward pass of a Spanish causal LM
(mrm8488/spanish-gpt2, a GPT-2-base trained from scratch on a 20GB Spanish
corpus) over the document, split into non-overlapping
token chunks that fit the model's context window. Sharing the forward pass
avoids doubling compute/RAM cost for a second "independent" source.

Calibration note: the perplexity->score mapping below uses heuristic reference
constants (not fit on labeled data). They are a reasonable starting point and
should be tuned with real human/AI Spanish text samples before relying on
absolute thresholds in production.
"""

import math
import re
import statistics

import torch
import torch.nn.functional as F

from . import DetectorOutput

_SENTENCE_SPLIT_RE = re.compile(r"[.!?…]+[\s\n]+")

# Heuristic reference perplexity/scale for the sigmoid mapping (see module docstring).
# mrm8488/spanish-gpt2 reports ~11.36 perplexity on its own held-out training-domain
# text; general-purpose documents (essays, articles) tend to score higher, hence the
# reference sits above that baseline. Tune with real labeled samples.
_PPL_REFERENCE = 25.0
_PPL_SCALE = 10.0
_BURST_TARGET_CV = 1.5


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _sentence_char_spans(text: str) -> list[tuple[int, int]]:
    spans = []
    pos = 0
    for sentence in _SENTENCE_SPLIT_RE.split(text):
        if not sentence.strip():
            continue
        start = text.find(sentence, pos)
        if start == -1:
            continue
        end = start + len(sentence)
        spans.append((start, end))
        pos = end
    return spans


class PerplexityDetector:
    def __init__(self, tokenizer, model, max_tokens_for_analysis: int = 3072):
        self.tokenizer = tokenizer
        self.model = model
        self.max_tokens_for_analysis = max_tokens_for_analysis
        context_window = getattr(model.config, "n_positions", None) or getattr(
            model.config, "n_ctx", 1024
        )
        self.chunk_size = context_window - 1
        self.vocab_size = model.config.vocab_size

    @torch.inference_mode()
    def analyze(self, text: str) -> tuple[DetectorOutput, DetectorOutput]:
        encoding = self.tokenizer(text, return_offsets_mapping=True, add_special_tokens=False)
        input_ids: list[int] = encoding["input_ids"]
        offsets: list[tuple[int, int]] = encoding["offset_mapping"]

        truncated = len(input_ids) > self.max_tokens_for_analysis
        input_ids = input_ids[: self.max_tokens_for_analysis]
        offsets = offsets[: self.max_tokens_for_analysis]

        per_token_nll: list[float] = []
        per_token_start_offset: list[int] = []
        rank_top10 = 0
        rank_top100 = 0
        total_tokens = 0
        entropy_sum = 0.0

        for chunk_start in range(0, len(input_ids), self.chunk_size):
            chunk_ids = input_ids[chunk_start : chunk_start + self.chunk_size]
            chunk_offsets = offsets[chunk_start : chunk_start + self.chunk_size]
            if len(chunk_ids) < 2:
                continue

            ids_tensor = torch.tensor([chunk_ids], dtype=torch.long)
            logits = self.model(input_ids=ids_tensor).logits[0]  # [seq_len, vocab]

            pred_logits = logits[:-1]  # predictions for positions 1..end
            actual_next = ids_tensor[0, 1:]  # the tokens actually observed

            log_probs = F.log_softmax(pred_logits, dim=-1)
            probs = log_probs.exp()
            entropy = -(probs * log_probs).sum(dim=-1)  # [seq_len-1]

            actual_logits = pred_logits.gather(1, actual_next.unsqueeze(1)).squeeze(1)
            ranks = (pred_logits > actual_logits.unsqueeze(1)).sum(dim=-1) + 1

            nll = -log_probs.gather(1, actual_next.unsqueeze(1)).squeeze(1)

            per_token_nll.extend(nll.tolist())
            per_token_start_offset.extend(o[0] for o in chunk_offsets[1:])
            rank_top10 += int((ranks <= 10).sum().item())
            rank_top100 += int((ranks <= 100).sum().item())
            entropy_sum += float(entropy.sum().item())
            total_tokens += nll.shape[0]

        if total_tokens == 0:
            zero = DetectorOutput(
                id="perplexity", name="Perplejidad y burstiness (LM español)",
                score=0.5, details="Texto demasiado corto para analizar de forma confiable.",
            )
            zero_rank = DetectorOutput(
                id="token_rank", name="Predictibilidad de tokens (estilo GLTR)",
                score=0.5, details="Texto demasiado corto para analizar de forma confiable.",
            )
            return zero, zero_rank

        avg_nll = sum(per_token_nll) / total_tokens
        perplexity = math.exp(min(avg_nll, 20))  # cap to avoid overflow on pathological input

        score_ppl_level = 1 / (1 + math.exp((perplexity - _PPL_REFERENCE) / _PPL_SCALE))

        sentence_spans = _sentence_char_spans(text[: offsets[-1][1] if offsets else len(text)])
        sentence_nlls: list[float] = []
        if sentence_spans:
            span_idx = 0
            bucket: list[float] = []
            for start_offset, nll_value in zip(per_token_start_offset, per_token_nll):
                while span_idx < len(sentence_spans) - 1 and start_offset >= sentence_spans[span_idx][1]:
                    if bucket:
                        sentence_nlls.append(statistics.mean(bucket))
                    bucket = []
                    span_idx += 1
                bucket.append(nll_value)
            if bucket:
                sentence_nlls.append(statistics.mean(bucket))

        if len(sentence_nlls) >= 3:
            mean_nll = statistics.mean(sentence_nlls)
            cv = statistics.pstdev(sentence_nlls) / mean_nll if mean_nll > 0 else 0.0
            score_burst = _clamp(1 - min(cv, _BURST_TARGET_CV) / _BURST_TARGET_CV)
        else:
            cv = 0.0
            score_burst = 0.5

        score_b = _clamp(0.6 * score_ppl_level + 0.4 * score_burst)

        details_b = (
            f"Perplejidad promedio: {perplexity:.1f} (referencia heurística: {_PPL_REFERENCE:.0f}). "
            f"Variación de predictibilidad entre oraciones (CV): {cv:.2f}."
        )
        if truncated:
            details_b += " Análisis limitado a los primeros fragmentos del documento por rendimiento."

        source_b = DetectorOutput(
            id="perplexity", name="Perplejidad y burstiness (LM español)", score=score_b, details=details_b,
        )

        frac_top10 = rank_top10 / total_tokens
        frac_top100 = rank_top100 / total_tokens
        mean_entropy = entropy_sum / total_tokens
        normalized_entropy = _clamp(mean_entropy / math.log(self.vocab_size))

        score_c = _clamp(0.6 * frac_top10 + 0.4 * (1 - normalized_entropy))

        details_c = (
            f"Tokens en el top-10 más probable del modelo: {frac_top10 * 100:.0f}%. "
            f"Tokens en el top-100: {frac_top100 * 100:.0f}%. "
            f"Entropía normalizada promedio: {normalized_entropy:.2f}. "
            "Inspirado en GLTR; no es una implementación literal del método Binoculars."
        )

        source_c = DetectorOutput(
            id="token_rank", name="Predictibilidad de tokens (estilo GLTR)", score=score_c, details=details_c,
        )

        return source_b, source_c
