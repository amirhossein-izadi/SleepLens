/* eslint no-console: ["error", { allow: ["error"] }] */

const isDev = process.env.NODE_ENV === "development";

function log(level: "info" | "warn" | "error", message: string, detail?: unknown) {
  if (!isDev && level !== "error") return;
  const payload: unknown[] = [message];
  if (detail !== undefined) payload.push(detail);
  // eslint-disable-next-line no-console
  console[level](...payload);
}

export const logger = {
  info: (message: string, detail?: unknown) => log("info", message, detail),
  warn: (message: string, detail?: unknown) => log("warn", message, detail),
  error: (message: string, detail?: unknown) => log("error", message, detail),
};
