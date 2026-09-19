export interface SourceResult {
  id: string;
  name: string;
  score: number;
  label: string;
  weight: number;
  details: string;
}

export interface AnalyzeResponse {
  overall_score: number;
  label: string;
  sources: SourceResult[];
  warnings: string[];
  disclaimer: string;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export async function analyzeDocument(file: File): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append("file", file);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: "POST",
      body: formData,
    });
  } catch {
    throw new ApiError(0, "No se pudo conectar con el servidor. Revisá tu conexión e intentá de nuevo.");
  }

  if (!response.ok) {
    let detail = "Ocurrió un error al analizar el documento.";
    try {
      const body = await response.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // ignore body parse errors, use default message
    }
    throw new ApiError(response.status, detail);
  }

  return response.json();
}
