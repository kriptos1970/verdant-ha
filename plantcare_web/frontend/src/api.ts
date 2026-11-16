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
    let message = `Operazione non riuscita (HTTP ${response.status}). Riprova.`;
    try {
      const body = await response.json();
      message =
        typeof body.detail === "string"
          ? body.detail
          : "Controlla i dati inseriti.";
    } catch {
      if (response.status === 401 || response.status === 403)
        message = "Sessione scaduta. Riapri PlantCare da Home Assistant.";
    }
    throw new Error(message);
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
