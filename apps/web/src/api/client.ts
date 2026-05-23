import type { ApiError, ParserMetadata, StatementParseResponse } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function fetchParsers(): Promise<ParserMetadata[]> {
  const response = await fetch(`${API_BASE_URL}/api/parsers`);
  if (!response.ok) {
    throw await toApiError(response);
  }
  return response.json();
}

export async function parseStatement(input: {
  file: File;
  password?: string;
  parserName?: string;
}): Promise<StatementParseResponse> {
  const form = new FormData();
  form.append("file", input.file);
  if (input.password) {
    form.append("password", input.password);
  }
  if (input.parserName) {
    form.append("parser_name", input.parserName);
  }

  const response = await fetch(`${API_BASE_URL}/api/statements/parse`, {
    method: "POST",
    body: form,
  });
  if (!response.ok) {
    throw await toApiError(response);
  }
  return response.json();
}

export async function exportStatement(input: {
  file: File;
  password?: string;
  parserName?: string;
  format: "tsv" | "csv";
}): Promise<Blob> {
  const form = new FormData();
  form.append("file", input.file);
  if (input.password) {
    form.append("password", input.password);
  }
  if (input.parserName) {
    form.append("parser_name", input.parserName);
  }

  const response = await fetch(
    `${API_BASE_URL}/api/statements/export?format=${input.format}`,
    { method: "POST", body: form },
  );
  if (!response.ok) {
    throw await toApiError(response);
  }
  return response.blob();
}

async function toApiError(response: Response): Promise<ApiError> {
  try {
    return (await response.json()) as ApiError;
  } catch {
    return {
      error: "REQUEST_FAILED",
      message: `Request failed with status ${response.status}`,
    };
  }
}
