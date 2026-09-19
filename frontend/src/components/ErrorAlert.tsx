interface ErrorAlertProps {
  message: string;
  onRetry: () => void;
}

export default function ErrorAlert({ message, onRetry }: ErrorAlertProps) {
  return (
    <div className="error-alert" role="alert">
      <p>{message}</p>
      <button type="button" onClick={onRetry} className="button button--secondary">
        Intentar de nuevo
      </button>
    </div>
  );
}
