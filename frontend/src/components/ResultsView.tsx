import { labelClass } from "../labelColor";
import type { AnalyzeResponse } from "../api/client";
import SourceCard from "./SourceCard";

interface ResultsViewProps {
  result: AnalyzeResponse;
  fileName: string;
  onAnalyzeAnother: () => void;
}

export default function ResultsView({ result, fileName, onAnalyzeAnother }: ResultsViewProps) {
  return (
    <div className="results-view">
      <div className="overall-card">
        <p className="overall-card__file">{fileName}</p>
        <div className="overall-card__score">{result.overall_score}%</div>
        <span className={`badge badge--large ${labelClass(result.label)}`}>{result.label}</span>
        <p className="overall-card__caption">probabilidad estimada de contenido generado por IA</p>
      </div>

      {result.warnings.length > 0 && (
        <div className="warnings">
          {result.warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      )}

      <h2 className="section-title">Detalle por fuente</h2>
      <div className="source-grid">
        {result.sources.map((source) => (
          <SourceCard key={source.id} source={source} />
        ))}
      </div>

      <button type="button" onClick={onAnalyzeAnother} className="button button--primary">
        Analizar otro documento
      </button>
    </div>
  );
}
