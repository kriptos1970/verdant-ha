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
import { Avatar, Modal, eventIcon } from "./ui";
import { useI18n } from "./i18n";
import { useCareLabels } from "./care-labels";

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
  const { t, plural, locale } = useI18n();
  const { actionLabel } = useCareLabels();
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
    a.localeCompare(b, locale),
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
        a.room.localeCompare(b.room, locale) ||
        a.dueDate.localeCompare(b.dueDate) ||
        a.plantName.localeCompare(b.plantName, locale) ||
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
    <Modal title={t("round.title")} onClose={onClose}>
      {stage === "setup" ? (
        <div className="round-setup">
          <div className="round-symbol">
            <Droplets size={31} />
          </div>
          <h3>{t("round.setupTitle")}</h3>
          <p>{t("round.setupText")}</p>
          <label>
            {t("round.room")}
            <select
              value={selectedRoom}
              onChange={(e) => setSelectedRoom(e.target.value)}
            >
              <option value="Tutte">{t("round.allRooms")}</option>
              {rooms.map((r) => (
                <option key={r}>{r}</option>
              ))}
            </select>
          </label>
          <div className="round-ready">
            <strong>{pending.length}</strong>
            <span>
              {plural("round.tasks", pending.length)} ·{" "}
              {plural("round.plants", new Set(pending.map((a) => a.plantID)).size)}
            </span>
          </div>
          <button
            className="button primary"
            disabled={!pending.length}
            onClick={start}
          >
            {t("round.start")} <ChevronRight size={17} />
          </button>
          {!pending.length && (
            <p className="muted">
              {t("round.empty")}
            </p>
          )}
        </div>
      ) : finished ? (
        <div className="round-finish" role="status">
          <CheckCircle2 size={55} />
          <h3>{t("round.finishedTitle")}</h3>
          <p>{plural("round.completed", stats.completed)}</p>
          <dl>
            <div>
              <dt>{t("round.postponed")}</dt>
              <dd>{stats.postponed}</dd>
            </div>
            <div>
              <dt>{t("round.skipped")}</dt>
              <dd>{stats.skipped}</dd>
            </div>
            {stats.changed > 0 && (
              <div>
                <dt>{t("round.changed")}</dt>
                <dd>{stats.changed}</dd>
              </div>
            )}
          </dl>
          <p className="muted">{t("round.finishedNote")}</p>
          <div className="button-row">
            <button
              className="button secondary"
              onClick={() => setStage("setup")}
            >
              {t("round.back")}
            </button>
            <button className="button primary" onClick={onClose}>
              {t("common.close")}
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
              {t("round.of", { current: index + 1, total: queue.length })}
            </span>
          </div>
          <progress
            aria-label={t("round.progress")}
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
              {t("round.caution")}
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
                {t("round.feedTogether")}
              </label>
            )}
          <label>
            {t("round.note")}
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
                {t("round.refresh")}
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
              {t("round.complete")}
            </button>
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => void record("postpone")}
            >
              <Clock3 size={18} />
              {t("round.postpone")}
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
              {t("round.skip")}
            </button>
          </div>
          <small className="muted">{t("round.zone", { zone })}</small>
        </div>
      ) : (
        <p className="muted">{t("round.updating")}</p>
      )}
    </Modal>
  );
}
