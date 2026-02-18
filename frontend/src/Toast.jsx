import { useEffect } from "react";

const TOAST_DURATION_MS = 4000;

export function Toast({ message, type = "error", onDismiss }) {
  useEffect(() => {
    const t = setTimeout(onDismiss, TOAST_DURATION_MS);
    return () => clearTimeout(t);
  }, [onDismiss]);

  if (!message) return null;

  return (
    <div
      className={`toast toast--${type}`}
      role="alert"
      aria-live="polite"
    >
      {message}
    </div>
  );
}
