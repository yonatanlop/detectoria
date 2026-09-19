export default function ProgressIndicator({ fileName }: { fileName: string }) {
  return (
    <div className="progress-indicator">
      <div className="spinner" aria-hidden="true" />
      <p>
        Analizando <strong>{fileName}</strong>…
      </p>
      <p className="progress-indicator__hint">
        Esto puede tardar hasta 30 segundos: el análisis corre modelos de lenguaje sobre CPU.
      </p>
    </div>
  );
}
