import { labelClass } from "../labelColor";
import type { SourceResult } from "../api/client";

export default function SourceCard({ source }: { source: SourceResult }) {
  return (
    <div className="source-card">
      <div className="source-card__header">
        <h3>{source.name}</h3>
        <span className={`badge ${labelClass(source.label)}`}>{source.label}</span>
      </div>
      <div className="source-card__score-row">
        <div className="score-bar">
          <div className="score-bar__fill" style={{ width: `${source.score}%` }} />
        </div>
        <span className="source-card__score-value">{source.score}%</span>
      </div>
      <p className="source-card__details">{source.details}</p>
      <p className="source-card__weight">Peso en el resultado final: {(source.weight * 100).toFixed(0)}%</p>
    </div>
  );
}
