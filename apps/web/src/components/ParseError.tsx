import { AlertTriangle, RotateCcw } from "lucide-react";

import type { ApiError } from "../api/types";

type ParseErrorProps = {
  error: ApiError;
  onRetry: () => void;
};

export function ParseError({ error, onRetry }: ParseErrorProps) {
  return (
    <section className="state-panel error-panel">
      <AlertTriangle aria-hidden="true" size={28} />
      <div>
        <h2>Could Not Parse Statement</h2>
        <strong>{friendlyTitle(error.error)}</strong>
        <p>{error.message}</p>
        <button className="secondary-action" onClick={onRetry}>
          <RotateCcw size={16} />
          Try Again
        </button>
      </div>
    </section>
  );
}

function friendlyTitle(code: string) {
  switch (code) {
    case "PDF_DECRYPT_FAILED":
      return "Wrong or missing password";
    case "UNSUPPORTED_FILE":
      return "File is not a PDF";
    case "UNSUPPORTED_STATEMENT":
      return "Unsupported statement format";
    default:
      return "Parser error";
  }
}
