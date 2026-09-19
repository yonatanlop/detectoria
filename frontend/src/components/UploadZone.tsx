import { useCallback, useState } from "react";
import { useDropzone, type FileRejection } from "react-dropzone";

const ACCEPTED_EXTENSIONS = [".txt", ".pdf", ".docx"];
const MAX_SIZE_BYTES = 8 * 1024 * 1024;

interface UploadZoneProps {
  onFileAccepted: (file: File) => void;
}

export default function UploadZone({ onFileAccepted }: UploadZoneProps) {
  const [localError, setLocalError] = useState<string | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[], fileRejections: FileRejection[]) => {
      setLocalError(null);

      if (fileRejections.length > 0) {
        setLocalError("Formato no soportado o archivo demasiado grande (máx. 8MB). Usá TXT, PDF o DOCX.");
        return;
      }

      const file = acceptedFiles[0];
      if (!file) return;

      const lowerName = file.name.toLowerCase();
      const hasValidExtension = ACCEPTED_EXTENSIONS.some((ext) => lowerName.endsWith(ext));
      if (!hasValidExtension) {
        setLocalError("Formato no soportado. Usá TXT, PDF o DOCX.");
        return;
      }
      if (file.size > MAX_SIZE_BYTES) {
        setLocalError("El archivo supera el tamaño máximo permitido (8MB).");
        return;
      }

      onFileAccepted(file);
    },
    [onFileAccepted]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles: 1,
    maxSize: MAX_SIZE_BYTES,
    accept: {
      "text/plain": [".txt"],
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
  });

  return (
    <div>
      <div {...getRootProps()} className={`upload-zone ${isDragActive ? "upload-zone--active" : ""}`}>
        <input {...getInputProps()} />
        <p className="upload-zone__title">
          {isDragActive ? "Soltá el archivo acá..." : "Arrastrá un documento o hacé clic para seleccionarlo"}
        </p>
        <p className="upload-zone__hint">Formatos aceptados: TXT, PDF, DOCX — máximo 8MB</p>
      </div>
      {localError && <p className="upload-zone__error">{localError}</p>}
    </div>
  );
}
