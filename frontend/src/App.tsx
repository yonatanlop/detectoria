import { useCallback, useState } from "react";

import { analyzeDocument, ApiError, type AnalyzeResponse } from "./api/client";
import DisclaimerBanner from "./components/DisclaimerBanner";
import ErrorAlert from "./components/ErrorAlert";
import ProgressIndicator from "./components/ProgressIndicator";
import ResultsView from "./components/ResultsView";
import UploadZone from "./components/UploadZone";

type Status = "idle" | "analyzing" | "done" | "error";

export default function App() {
  const [status, setStatus] = useState<Status>("idle");
  const [fileName, setFileName] = useState<string>("");
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>("");

  const handleFileAccepted = useCallback(async (file: File) => {
    setFileName(file.name);
    setStatus("analyzing");
    try {
      const response = await analyzeDocument(file);
      setResult(response);
      setStatus("done");
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Ocurrió un error inesperado.";
      setErrorMessage(message);
      setStatus("error");
    }
  }, []);

  const reset = useCallback(() => {
    setStatus("idle");
    setResult(null);
    setErrorMessage("");
    setFileName("");
  }, []);

  return (
    <div className="app">
      <header className="app__header">
        <h1>DetectorIA</h1>
        <p>Analizá documentos con varias fuentes independientes para estimar si fueron escritos por IA.</p>
      </header>

      <DisclaimerBanner />

      <main className="app__main">
        {status === "idle" && <UploadZone onFileAccepted={handleFileAccepted} />}
        {status === "analyzing" && <ProgressIndicator fileName={fileName} />}
        {status === "error" && <ErrorAlert message={errorMessage} onRetry={reset} />}
        {status === "done" && result && (
          <ResultsView result={result} fileName={fileName} onAnalyzeAnother={reset} />
        )}
      </main>
    </div>
  );
}
