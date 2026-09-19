from ..config import Settings
from ..schemas import SourceResult
from . import DetectorOutput

DISCLAIMER = (
    "Este resultado es un indicador probabilístico, no una prueba. Los detectores de "
    "texto generado por IA -incluso los de pago- tienen tasas reales de falsos "
    "positivos y son menos confiables con textos cortos, traducidos, muy editados o "
    "de personas que no escriben en su lengua nativa. No debe usarse como única "
    "evidencia para una acusación académica o disciplinaria."
)


def score_to_label(score_0_100: int, settings: Settings) -> str:
    if score_0_100 <= settings.threshold_human_max:
        return "Humano"
    if score_0_100 <= settings.threshold_ai_hints_max:
        return "Indicios de IA"
    return "Probable IA"


def aggregate(outputs: list[DetectorOutput], settings: Settings) -> tuple[int, str, list[SourceResult]]:
    weights = settings.source_weights()

    sources: list[SourceResult] = []
    weighted_sum = 0.0
    total_weight = 0.0

    for output in outputs:
        weight = weights.get(output.id, 0.0)
        score_pct = round(output.score * 100)
        sources.append(
            SourceResult(
                id=output.id,
                name=output.name,
                score=score_pct,
                label=score_to_label(score_pct, settings),
                weight=weight,
                details=output.details,
            )
        )
        weighted_sum += weight * output.score
        total_weight += weight

    overall_score = round(100 * (weighted_sum / total_weight)) if total_weight > 0 else 0
    overall_label = score_to_label(overall_score, settings)

    return overall_score, overall_label, sources
