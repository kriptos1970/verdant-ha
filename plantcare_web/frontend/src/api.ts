const EN_DETAILS: Record<string, string> = {
  "La scheda è cambiata. Ricarica prima di salvare.": "The record changed. Reload before saving.",
  "La scheda è cambiata. Ricarica prima di applicare il piano.": "The record changed. Reload before applying the plan.",
  "Elemento non trovato.": "Item not found.",
  "Elemento non più disponibile.": "Item is no longer available.",
  "Tipo di cura non valido": "Invalid care type.",
  "Tipo di cura sconosciuto": "Unknown care type.",
  "Stato di salute non valido.": "Invalid plant condition.",
  "Data di rinvio non valida.": "Invalid postponement date.",
  "Il rinvio deve essere successivo alla data della cura.": "The postponement must be later than the care date.",
  "Questa attività è cambiata. Ricarica il calendario prima di registrarla.": "This task changed. Reload the calendar before recording it.",
  "L’attività è cambiata durante il giro. Aggiorna le attività prima di continuare.": "The task changed during the round. Refresh the tasks before continuing.",
  "Questa applicazione è già stata registrata o il ciclo è cambiato. Ricarica la scheda.": "This application was already recorded or the cycle changed. Reload the plant.",
  "Il ciclo non è più attivo.": "The cycle is no longer active.",
  "Ciclo di trattamento non trovato.": "Treatment cycle not found.",
  "La pianta è cambiata. Riapri il controllo prima di salvare.": "The plant changed. Reopen the check before saving.",
  "Identificativo del controllo già utilizzato con dati diversi.": "This check id was already used with different data.",
  "Identificativo del controllo già presente nella cronologia.": "This check id is already in the history.",
  "Una fotografia non è disponibile. Riprova il caricamento.": "A photo is unavailable. Try uploading it again.",
  "Fotografia non disponibile.": "Photo not available.",
  "Immagine non supportata. Usa JPEG, PNG o WebP.": "Unsupported image. Use JPEG, PNG or WebP.",
  "Fotografia oltre il limite configurato.": "Photo exceeds the configured limit.",
  "Spazio insufficiente nella cartella delle foto.": "Not enough space in the photo folder.",
  "Configura provider e chiave AI nelle opzioni dell’add-on.": "Configure the AI provider and key in the add-on options.",
  "Configura provider e chiave nelle opzioni dell’add-on.": "Configure the provider and key in the add-on options.",
  "Analisi già in corso.": "An analysis is already running.",
  "Una richiesta all’assistente è già in corso. Attendi il risultato.": "An assistant request is already running. Wait for the result.",
  "La scheda è cambiata durante l’analisi. Richiedi un nuovo consiglio.": "The plant changed during the analysis. Request new advice.",
  "Il consiglio è cambiato. Richiedi una nuova analisi.": "The advice changed. Request a new analysis.",
  "Piano o cronologia cambiati dopo l’analisi. Richiedi un nuovo consiglio.": "The plan or history changed after the analysis. Request new advice.",
  "Il contesto del consiglio è cambiato. Richiedi una nuova analisi.": "The advice context changed. Request a new analysis.",
  "Modello non presente nel catalogo di questo provider.": "The model is not in this provider's catalog.",
  "Apri la scheda completa prima di modificarla.": "Open the full plant before editing it.",
  "Identificativo non corrispondente.": "Identifier mismatch.",
  "Pianta non trovata.": "Plant not found.",
  "Backup oltre il limite di 2 GB.": "Backup exceeds the 2 GB limit.",
  "Importazione disponibile soltanto su archivio vuoto.": "Import is available only into an empty archive.",
  "Il ripristino completo richiede un backup web. I backup nativi si importano soltanto su un archivio vuoto.": "A full restore needs a web backup. Native backups can only be imported into an empty archive.",
};

const EN_ERRORS: Record<string, string> = {
  bad_request: "Invalid request.",
  unauthorized: "Session expired. Open PlantCare from Home Assistant again.",
  forbidden: "Access is allowed only through Home Assistant.",
  not_found: "Item not found.",
  conflict: "The data changed. Reload and try again.",
  too_large: "The request is too large.",
  validation: "Check the data and try again.",
  server: "Server temporarily unavailable. Try again shortly.",
  network: "Cannot connect to Verdant. Check your connection and try again.",
  invalid_response: "Unexpected server response. Reopen Verdant from Home Assistant.",
  remote: "An external service is temporarily unavailable. Try again shortly.",
  error: "The operation failed. Try again.",
};

const IT_ERRORS: Record<string, string> = {
  bad_request: "Richiesta non valida.",
  unauthorized: "Sessione scaduta. Riapri Verdant da Home Assistant.",
  forbidden: "Accesso consentito soltanto tramite Home Assistant.",
  not_found: "Elemento non trovato.",
  conflict: "I dati sono cambiati. Ricarica e riprova.",
  too_large: "La richiesta supera il limite consentito.",
  validation: "La richiesta non è valida. Verifica i campi indicati e riprova.",
  server: "Server temporaneamente non disponibile. Riprova tra poco.",
  network: "Impossibile connettersi a Verdant. Controlla la connessione e riprova.",
  invalid_response: "Risposta del server inattesa. Riapri Verdant da Home Assistant.",
  remote: "Un servizio esterno non è temporaneamente disponibile. Riprova tra poco.",
  error: "Operazione non riuscita. Riprova.",
};

function detailMessage(detail: unknown): string {
  if (typeof detail === "string") return detail.trim();
  if (!Array.isArray(detail)) return "";
  return detail.slice(0, 3).flatMap(item => {
    if (!item || typeof item.msg !== "string") return [];
    const field = Array.isArray(item.loc)
      ? item.loc.filter((part: unknown) => !["body", "query", "path"].includes(String(part))).join(".")
      : "";
    const message = item.msg.replace(/^Value error, /, "").trim();
    return message ? [field ? `${field}: ${message}` : message] : [];
  }).join("; ");
}

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
  const message = detailMessage(detail);
  const english = activeLanguage() === "en";
  // Never replace a useful server detail with a generic translation.
  if (message) return english ? EN_DETAILS[message] || message : message;
  const messages = english ? EN_ERRORS : IT_ERRORS;
  return messages[code] || messages.error;
}

function apiError(code: string, detail?: unknown, status?: number) {
  return Object.assign(new Error(errorMessage(code, detail)), { code, status });
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("X-PlantCare-Request", "1");
  if (options.body && !(options.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  let response: Response;
  try {
    response = await fetch(`api/${path}`, { ...options, headers });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") throw error;
    throw apiError("network");
  }
  if (!response.ok) {
    const statusCodes: Record<number, string> = {
      400: "bad_request", 401: "unauthorized", 403: "forbidden",
      404: "not_found", 409: "conflict", 413: "too_large",
      422: "validation", 424: "remote",
    };
    let code = statusCodes[response.status] || (response.status >= 500 ? "server" : "error");
    let detail: unknown;
    try {
      const body = await response.json();
      if (body && typeof body.code === "string") code = body.code;
      detail = body?.detail;
    } catch {
      // Keep the status-derived code.
    }
    throw apiError(code, detail, response.status);
  }
  if (response.status === 204) return undefined as T;
  try {
    return await response.json();
  } catch {
    throw apiError("invalid_response", undefined, response.status);
  }
}
export const photoURL = (path?: string | null, thumb = false) =>
  path && /^[a-f0-9]{64}\.jpg$/.test(path)
    ? `api/photos/${path}${thumb ? "?thumb=true" : ""}`
    : undefined;
export const uid = () => crypto.randomUUID().toUpperCase();
export const todayISO = () => new Date().toISOString();
