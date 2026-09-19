from dataclasses import dataclass


@dataclass
class DetectorOutput:
    id: str
    name: str
    score: float  # 0.0-1.0, probability the text is AI-generated
    details: str
