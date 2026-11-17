const EN_ERRORS: Record<string, string> = {
  bad_request: "Invalid request.",
  unauthorized: "Session expired. Open PlantCare from Home Assistant again.",
  forbidden: "Access is allowed only through Home Assistant.",
  not_found: "Item not found.",
  conflict: "The data changed. Reload and try again.",
  too_large: "The request is too large.",
  validation: "Check the data and try again.",
  error: "The operation failed. Try again.",
};

function activeLanguage() {
  try {
    const preference = localStorage.getItem("plantcare.language");
    if (preference === "it" || preference === "en") return preference;
  } catch {
    // Private mode: fall back to the document or browser language.
  }
  const language = (
    document.documentElement.lang ||
    navigator.language ||
    ""
  ).toLowerCase();
  return language.startsWith("it") ? "it" : "en";
}

function errorMessage(code: string, detail: unknown) {
  if (activeLanguage() === "en" && EN_ERRORS[code]) return EN_ERRORS[code];
  if (typeof detail === "string" && detail) return detail;
  return activeLanguage() === "en"
    ? "Check the data and try again."
    : "Controlla i dati inseriti.";
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("X-PlantCare-Request", "1");
  if (options.body && !(options.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  const response = await fetch(`api/${path}`, { ...options, headers });
  if (!response.ok) {
    let code =
      response.status === 401
        ? "unauthorized"
        : response.status === 403
          ? "forbidden"
          : "error";
    let detail: unknown;
    try {
      const body = await response.json();
      if (typeof body.code === "string") code = body.code;
      detail = body.detail;
    } catch {
      // Keep the status-derived code.
    }
    throw new Error(errorMessage(code, detail));
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}
export const photoURL = (path?: string | null, thumb = false) =>
  path && /^[a-f0-9]{64}\.jpg$/.test(path)
    ? `api/photos/${path}${thumb ? "?thumb=true" : ""}`
    : undefined;
export const uid = () => crypto.randomUUID().toUpperCase();
export const todayISO = () => new Date().toISOString();
export const dateLabel = (date: string) =>
  new Date(date).toLocaleDateString("it-IT", {
    day: "numeric",
    month: "short",
  });
export const dueLabel = (days: number) =>
  days < 0
    ? `${Math.abs(days)} g in ritardo`
    : days === 0
      ? "Oggi"
      : days === 1
        ? "Domani"
        : `Tra ${days} giorni`;
