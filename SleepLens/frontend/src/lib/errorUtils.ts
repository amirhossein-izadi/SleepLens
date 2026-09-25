/**
 * Error extraction utility for API error responses.
 * Handles { error }, { detail }, { message }, DRF field errors and axios errors.
 */

interface ApiErrorResponse {
  response?: {
    data?: {
      error?: string | { detail?: string; message?: string; details?: unknown } | null;
      detail?: string;
      message?: string;
    } | null;
    status?: number;
  };
  details?: unknown;
  message?: string;
}

export function extractErrorMessage(err: unknown, fallback = "An error occurred"): string {
  if (!err) return fallback;
  if (typeof err === "string") return err;
  if (err instanceof Error) return err.message || fallback;

  const apiError = err as ApiErrorResponse;
  const data = apiError?.response?.data;
  if (data) {
    if (typeof data.error === "string") return data.error;
    if (data.error && typeof data.error === "object") {
      if (data.error.message) return data.error.message;
      if (data.error.detail) return data.error.detail;
      const firstDetail = Array.isArray(data.error.details)
        ? (data.error.details[0] as { message?: string } | undefined)
        : undefined;
      if (firstDetail?.message) return firstDetail.message;
    }
    if (data.detail) return data.detail;
    if (data.message) return data.message;
    const fieldMessage = Object.values(data as Record<string, unknown>).find(
      (value) => typeof value === "string" || Array.isArray(value)
    );
    if (typeof fieldMessage === "string") return fieldMessage;
    if (Array.isArray(fieldMessage) && typeof fieldMessage[0] === "string") return fieldMessage[0];
  }
  if (Array.isArray(apiError?.details)) {
    const first = apiError.details[0] as { message?: string } | undefined;
    if (first?.message) return first.message;
  }
  return apiError?.message || fallback;
}
