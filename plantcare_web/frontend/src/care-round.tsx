import { useEffect, useRef, useState } from "react";
import {
  CheckCircle2,
  Check,
  Droplets,
  MapPin,
  Clock3,
  ChevronRight,
  LoaderCircle,
  RotateCw,
} from "lucide-react";
import type { Action, Plant } from "./types";
import { api, uid } from "./api";
import { Avatar, Modal, actionLabel, eventIcon } from "./ui";

export function CareRound({
  plants,
  room,
  zone,
  onClose,
  reload,
}: {
  plants: Plant[];
  room: string;
  zone: string;
  onClose: () => void;
  reload: () => Promise<void>;
}) {
  const [stage, setStage] = useState<"setup" | "active">("setup");
  const [selectedRoom, setSelectedRoom] = useState(room);
  const [queue, setQueue] = useState<Action[]>([]),
    [index, setIndex] = useState(0);
  const [stats, setStats] = useState({
    completed: 0,
    postponed: 0,
    skipped: 0,
    changed: 0,
  });
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [includeFeed, setIncludeFeed] = useState(false),
    [note, setNote] = useState("");
  const commands = useRef(new Map<string, string>());
  const rooms = [...new Set(plants.map((p) => p.room))].sort((a, b) =>
    a.localeCompare(b, "it"),
  );
  const pending = plants
    .flatMap((p) => p._actions)
    .filter(
      (a) =>
        a.daysUntil === 0 &&
        (selectedRoom === "Tutte" || a.room === selectedRoom),
    )
    .sort(
      (a, b) =>
        a.room.localeCompare(b.room, "it") ||
        a.dueDate.localeCompare(b.dueDate) ||
        a.plantName.localeCompare(b.plantName, "it") ||
        a.id.localeCompare(b.id),
    );
  const current = queue[index];
  const plant = plants.find((p) => p.id === current?.plantID);
  const live = plant?._actions.find((a) => a.id === current?.id);
  const finished = stage === "active" && index >= queue.length;
  useEffect(() => {
    setIncludeFeed(false);
    setNote("");
  }, [current?.id]);
  useEffect(() => {
    if (stage === "active" && current && !live && !busy && !error) {
      setStats((s) => ({ ...s, changed: s.changed + 1 }));
      setIndex((i) => i + 1);
    }
  }, [stage, current, live, busy, error]);
  const start = () => {
    setQueue(pending);
    setIndex(0);
    setStats({ completed: 0, postponed: 0, skipped: 0, changed: 0 });
    setError("");
    commands.current.clear();
    setStage("active");
  };
  const record = async (operation: "complete" | "postpone") => {
    if (!current || busy) return;
    setBusy(true);
    setError("");
    const key = current.id + ":" + operation;
    let eventID = commands.current.get(key);
    if (!eventID) {
      eventID = uid();
      commands.current.set(key, eventID);
    }
    try {
      const result = await api<{ completedEvents: number; replayed: boolean }>(
        "care-round/actions",
        {
          method: "POST",
          body: JSON.stringify({
            plantID: current.plantID,
            eventID,
            expectedActionID: current.id,
            operation,
            includingFertilizing: includeFeed,
            note,
          }),
        },
      );
      setStats((s) => ({
        ...s,
        completed: s.completed + result.completedEvents,
        postponed: s.postponed + (operation === "postpone" ? 1 : 0),
      }));
      setIndex((i) => i + 1);
      await reload();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const Icon = eventIcon(current?.kind || "Annaffia");
  return (
    <Modal title="Giro di cure" onClose={onClose}>
      {stage === "setup" ? (
        <div className="round-setup">
          <div className="round-symbol">
            <Droplets size={31} />
          </div>
          <h3>Una stanza, una pianta alla volta.</h3>
          <p>
            Le attività di oggi, ordinate per ambiente. Le cure precedenti
            restano nel calendario.
          </p>
          <label>
            Ambiente
            <select
              value={selectedRoom}
              onChange={(e) => setSelectedRoom(e.target.value)}
            >
              <option>Tutte</option>
              {rooms.map((r) => (
                <option key={r}>{r}</option>
              ))}
            </select>
          </label>
          <div className="round-ready">
            <strong>{pending.length}</strong>
            <span>
              {pending.length === 1 ? "attività di oggi" : "attività di oggi"} ·{" "}
              {new Set(pending.map((a) => a.plantID)).size} piante
            </span>
          </div>
          <button
            className="button primary"
            disabled={!pending.length}
            onClick={start}
          >
            Inizia il giro <ChevronRight size={17} />
          </button>
          {!pending.length && (
            <p className="muted">
              Nessuna attività prevista oggi per questo ambiente.
            </p>
          )}
        </div>
      ) : finished ? (
        <div className="round-finish" role="status">
          <CheckCircle2 size={55} />
          <h3>Giro completato</h3>
          <p>
            Hai completato <strong>{stats.completed}</strong>{" "}
            {stats.completed === 1 ? "attività" : "attività"}.
          </p>
          <dl>
            <div>
              <dt>Rimandate a domani</dt>
              <dd>{stats.postponed}</dd>
            </div>
            <div>
              <dt>Saltate</dt>
              <dd>{stats.skipped}</dd>
            </div>
            {stats.changed > 0 && (
              <div>
                <dt>Già cambiate durante il giro</dt>
                <dd>{stats.changed}</dd>
              </div>
            )}
          </dl>
          <p className="muted">
            Le attività saltate restano disponibili. Nessuna cura è stata
            registrata per le attività cambiate altrove.
          </p>
          <div className="button-row">
            <button
              className="button secondary"
              onClick={() => setStage("setup")}
            >
              Torna agli ambienti
            </button>
            <button className="button primary" onClick={onClose}>
              Chiudi
            </button>
          </div>
        </div>
      ) : current && plant ? (
        <div className="round-current">
          <div className="round-progress-header">
            <span>
              <MapPin size={16} />
              {current.room}
            </span>
            <span>
              {index + 1} di {queue.length}
            </span>
          </div>
          <progress
            aria-label="Avanzamento del giro"
            max={queue.length}
            value={index}
          />
          <Avatar plant={plant} large />
          <h3>{plant.name}</h3>
          <p className="round-action-label">
            <Icon size={22} />
            {actionLabel(current)}
          </p>
          {current.reason && <p className="round-reason">{current.reason}</p>}
          {current.kind === "Annaffia" && (
            <p className="round-caution">
              Controlla che il substrato abbia bisogno d’acqua prima di
              annaffiare.
            </p>
          )}
          {current.kind === "Annaffia" &&
            (current.includesFertilizing || current.canIncludeFertilizing) && (
              <label className="check-label round-feeding">
                <input
                  type="checkbox"
                  checked={includeFeed}
                  onChange={(e) => setIncludeFeed(e.target.checked)}
                  disabled={busy}
                />
                Ho concimato insieme all’annaffiatura
              </label>
            )}
          <label>
            Note facoltative
            <textarea
              rows={2}
              maxLength={20000}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              disabled={busy}
            />
          </label>
          {error && (
            <div className="form-error" role="alert">
              <p>{error}</p>
              <button
                className="text-button"
                disabled={busy}
                onClick={() => {
                  setBusy(true);
                  void reload()
                    .then(() => setError(""))
                    .catch((e) => setError(e.message))
                    .finally(() => setBusy(false));
                }}
              >
                <RotateCw size={15} />
                Aggiorna le attività
              </button>
            </div>
          )}
          <div className="round-buttons">
            <button
              className="button primary"
              disabled={busy}
              onClick={() => void record("complete")}
            >
              {busy ? (
                <LoaderCircle size={18} className="spin" />
              ) : (
                <Check size={18} />
              )}
              Completata
            </button>
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => void record("postpone")}
            >
              <Clock3 size={18} />
              Rimanda a domani
            </button>
            <button
              className="text-button"
              disabled={busy}
              onClick={() => {
                setStats((s) => ({ ...s, skipped: s.skipped + 1 }));
                setError("");
                setIndex((i) => i + 1);
              }}
            >
              Salta
            </button>
          </div>
          <small className="muted">Calendario: {zone}</small>
        </div>
      ) : (
        <p className="muted">Aggiorno le attività del giro…</p>
      )}
    </Modal>
  );
}
