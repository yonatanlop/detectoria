export default function DisclaimerBanner({ text }: { text?: string }) {
  return (
    <div className="disclaimer-banner" role="note">
      <span className="disclaimer-icon" aria-hidden="true">
        ⚠
      </span>
      <p>
        {text ??
          "Este resultado es un indicador probabilístico, no una prueba. Los detectores de IA " +
            "tienen falsos positivos reales y no deben usarse como única evidencia de una acusación " +
            "académica o disciplinaria."}
      </p>
    </div>
  );
}
