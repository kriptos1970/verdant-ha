import { useState } from "react";
import {
  CalendarDays,
  Check,
  ChevronRight,
  FlaskConical,
  Pause,
  Play,
  Plus,
  Pencil,
  LoaderCircle,
} from "lucide-react";
import type {
  Plant,
  Product,
  Treatment,
  TreatmentDraft,
  Action,
} from "./types";
import { api, uid } from "./api";
import { Modal } from "./ui";
import { useI18n } from "./i18n";
import { useCareLabels } from "./care-labels";

const dateInput = (date: string) => {
  const d = new Date(date);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};
const dateISO = (date: string, end = false) =>
  new Date(date + (end ? "T23:59:59" : "T12:00:00")).toISOString();
const statusKeys = {
  active: "treatment.status.active",
  complete: "treatment.status.complete",
  ended: "treatment.status.ended",
  cancelled: "treatment.status.cancelled",
} as const;

export function TreatmentEditor({
  plants,
  products,
  initialPlant,
  initialProduct,
  plan,
  busy,
  onClose,
  onSave,
}: {
  plants: Plant[];
  products: Product[];
  initialPlant?: Plant;
  initialProduct?: Product;
  plan?: Treatment;
  busy: boolean;
  onClose: () => void;
  onSave: (plant: Plant, draft: TreatmentDraft) => Promise<void>;
}) {
  const { t, plural } = useI18n();
  const { dateLabel } = useCareLabels();
  const first =
    initialProduct ||
    products.find((p) => p.id === plan?.productID) ||
    products[0];
  const [id] = useState(plan?.id || uid()),
    [plantID, setPlantID] = useState(initialPlant?.id || ""),
    [productID, setProductID] = useState(plan?.productID || first?.id || "");
  const [start, setStart] = useState(
      dateInput(plan?.startDate || new Date().toISOString()),
    ),
    [interval, setInterval] = useState(
      plan?.intervalDays || first?.applicationIntervalDays || 7,
    ),
    [total, setTotal] = useState(plan?.totalApplications || 3);
  const [hasEnd, setHasEnd] = useState(Boolean(plan?.endDate)),
    [end, setEnd] = useState(
      dateInput(plan?.endDate || new Date().toISOString()),
    );
  const [dose, setDose] = useState(plan?.dose || first?.dosage || ""),
    [notes, setNotes] = useState(plan?.notes || ""),
    [error, setError] = useState("");
  const natural = new Date(start + "T12:00:00");
  natural.setDate(
    natural.getDate() + (Math.max(1, total) - 1) * Math.max(1, interval),
  );
  const final =
    hasEnd && end && dateISO(end, true) < natural.toISOString()
      ? new Date(dateISO(end, true))
      : natural;
  const chosen = products.find((p) => p.id === productID);
  return (
    <Modal
      title={plan ? t("treatment.editTitle") : t("treatment.planTitle")}
      onClose={onClose}
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          const plant = initialPlant || plants.find((p) => p.id === plantID);
          if (!plant) {
            setError(t("treatment.selectPlantError"));
            return;
          }
          void onSave(plant, {
            id,
            productID,
            startDate: dateISO(start),
            intervalDays: interval,
            totalApplications: total,
            endDate: hasEnd ? dateISO(end, true) : null,
            dose: dose.trim(),
            notes: notes.trim(),
          }).catch((e) => setError(e.message));
        }}
      >
        <fieldset className="native-form-section">
          <legend>{t("treatment.destination")}</legend>
          <label>
            {t("treatment.plant")}
            <select
              required
              value={plantID}
              disabled={Boolean(initialPlant)}
              onChange={(e) => setPlantID(e.target.value)}
            >
              <option value="">{t("treatment.select")}</option>
              {plants.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} · {p.room}
                </option>
              ))}
            </select>
          </label>
          <label>
            {t("treatment.product")}
            <select
              required
              value={productID}
              onChange={(e) => {
                setProductID(e.target.value);
                const p = products.find((p) => p.id === e.target.value);
                if (p && !plan) {
                  setInterval(p.applicationIntervalDays || 7);
                  setDose(p.dosage || "");
                }
              }}
            >
              {!products.some((p) => p.id === productID) && (
                <option value={productID}>
                  {plan?.productName || t("treatment.select")}
                </option>
              )}
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            {t("treatment.first")}
            <input
              type="date"
              required
              value={start}
              onChange={(e) => setStart(e.target.value)}
            />
          </label>
        </fieldset>
        <fieldset className="native-form-section">
          <legend>{t("treatment.duration")}</legend>
          <div className="form-grid">
            <label>
              {t("treatment.everyDays")}
              <input
                type="number"
                required
                min={1}
                max={365}
                value={interval}
                onChange={(e) => setInterval(Number(e.target.value))}
              />
            </label>
            <label>
              {t("treatment.total")}
              <input
                type="number"
                required
                min={Math.max(1, plan?.completedApplications || 0)}
                max={100}
                value={total}
                onChange={(e) => setTotal(Number(e.target.value))}
              />
            </label>
          </div>
          <label className="check-label">
            <input
              type="checkbox"
              checked={hasEnd}
              onChange={(e) => setHasEnd(e.target.checked)}
            />
            {t("treatment.setEnd")}
          </label>
          {hasEnd && (
            <label>
              {t("treatment.endBy")}
              <input
                type="date"
                required
                min={start}
                value={end}
                onChange={(e) => setEnd(e.target.value)}
              />
            </label>
          )}
          <p className="planned-end">
            <span>{t("treatment.lastPlanned")}</span>
            <strong>
              {Number.isFinite(final.getTime())
                ? dateLabel(final.toISOString())
                : "—"}
            </strong>
          </p>
          {plan && plan.completedApplications > 0 && (
            <p className="muted small-text">
              {plural("treatment.already", plan.completedApplications)}
            </p>
          )}
        </fieldset>
        <fieldset className="native-form-section">
          <legend>{t("treatment.instructions")}</legend>
          <label>
            {t("treatment.dose")}
            <input
              value={dose}
              maxLength={2000}
              onChange={(e) => setDose(e.target.value)}
              placeholder={t("treatment.dosePlaceholder")}
            />
          </label>
          <label>
            {t("treatment.notes")}
            <textarea
              rows={3}
              value={notes}
              maxLength={20000}
              onChange={(e) => setNotes(e.target.value)}
            />
          </label>
          {chosen?.applicationMethod && (
            <p className="muted small-text">
              {t("treatment.method", { method: chosen.applicationMethod })}
            </p>
          )}
        </fieldset>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <div className="modal-actions">
          <button type="button" className="button secondary" onClick={onClose}>
            {t("common.cancel")}
          </button>
          <button
            className="button primary"
            disabled={busy || !productID || !plantID}
          >
            {busy ? (
              <LoaderCircle className="spin" size={16} />
            ) : (
              <Check size={16} />
            )}
            {t("treatment.save")}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export function TreatmentPanel({
  plant,
  products,
  busy,
  run,
  onAction,
}: {
  plant: Plant;
  products: Product[];
  busy: boolean;
  run: (fn: () => Promise<unknown>, message?: string) => Promise<void>;
  onAction: (action: Action) => void;
}) {
  const { t, plural } = useI18n();
  const { dateLabel } = useCareLabels();
  const [editor, setEditor] = useState<Treatment | "new" | null>(null),
    [confirm, setConfirm] = useState<Treatment | null>(null),
    [error, setError] = useState("");
  return (
    <section className="treatment-panel">
      <div className="section-heading">
        <h3>{t("treatment.cycles")}</h3>
        <button
          className="icon-button"
          aria-label={t("treatment.newAria")}
          onClick={() => setEditor("new")}
          disabled={!products.length}
        >
          <Plus size={20} />
        </button>
      </div>
      <p className="muted small-text">
        {t("treatment.panelText")}
      </p>
      {!products.length && (
        <p className="info-note">
          {t("treatment.addProductFirst")}
        </p>
      )}
      {!plant._treatments.length ? (
        <div className="gentle-empty">
          <FlaskConical size={25} />
          <p>{t("treatment.none")}</p>
        </div>
      ) : (
        plant._treatments.map((plan) => {
          const action = plant._actions.find(
            (a) => a.treatmentPlanID === plan.id,
          );
          return (
            <article className="treatment-card" key={plan.id}>
              <div className="section-heading">
                <h3>{plan.productName}</h3>
                <span className={`pill treatment-status-${plan.status}`}>
                  {t(statusKeys[plan.status])}
                </span>
              </div>
              <div className="treatment-count">
                <strong>
                  {plan.completedApplications}
                  <small> / {plan.totalApplications}</small>
                </strong>
                <span>{t("treatment.applications")}</span>
              </div>
              <progress
                aria-label={t("treatment.progressAria", { name: plan.productName })}
                max={plan.totalApplications}
                value={plan.completedApplications}
              />
              <p className="muted small-text">
                {t("treatment.everyDaysLine", { interval: plan.intervalDays, start: dateLabel(plan.startDate) })}
                {plan.endDate ? t("treatment.until", { date: dateLabel(plan.endDate) }) : ""}
              </p>
              {plan.dose && (
                <p>
                  <strong>{t("treatment.dose")}</strong> {plan.dose}
                </p>
              )}
              {plan.notes && <p className="preserve">{plan.notes}</p>}
              {action && (
                <button
                  className="button primary treatment-register"
                  disabled={busy}
                  onClick={() => onAction(action)}
                >
                  <Check size={16} />
                  {t("treatment.register", { number: action.applicationNumber ?? 1 })}
                  <ChevronRight size={16} />
                </button>
              )}
              {plan.nextDueDate && (
                <p className="muted small-text">
                  {t("treatment.next", { date: dateLabel(plan.nextDueDate) })}
                </p>
              )}
              <div className="button-row">
                <button
                  className="text-button"
                  onClick={() => setEditor(plan)}
                  disabled={busy}
                >
                  <Pencil size={14} />
                  {t("treatment.editCycle")}
                </button>
                {plan.status === "active" && (
                  <button
                    className="text-button danger"
                    onClick={() => setConfirm(plan)}
                    disabled={busy}
                  >
                    <Pause size={14} />
                    {t("treatment.stop")}
                  </button>
                )}
                {plan.status === "cancelled" && (
                  <button
                    className="text-button"
                    disabled={busy}
                    onClick={() =>
                      void run(
                        () =>
                          api(
                            `plants/${plant.id}/treatments/${plan.id}/resume?version=${plant._version}`,
                            { method: "POST" },
                          ),
                        t("treatment.resumed"),
                      ).catch((e) => setError(e.message))
                    }
                  >
                    <Play size={14} />
                    {t("treatment.resume")}
                  </button>
                )}
              </div>
            </article>
          );
        })
      )}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      {editor && (
        <TreatmentEditor
          plants={[plant]}
          products={products}
          initialPlant={plant}
          plan={editor === "new" ? undefined : editor}
          busy={busy}
          onClose={() => setEditor(null)}
          onSave={async (p, draft) => {
            await run(
              () =>
                api(
                  `plants/${p.id}/treatments${editor === "new" ? "" : `/${draft.id}`}?version=${p._version}`,
                  {
                    method: editor === "new" ? "POST" : "PUT",
                    body: JSON.stringify(draft),
                  },
                ),
              editor === "new" ? t("treatment.planned") : t("treatment.updated"),
            );
            setEditor(null);
          }}
        />
      )}
      {confirm && (
        <Modal title={t("treatment.stopTitle")} onClose={() => setConfirm(null)}>
          <p>
            {t("treatment.stopText", { name: confirm.productName })}
          </p>
          <div className="modal-actions">
            <button
              className="button secondary"
              onClick={() => setConfirm(null)}
            >
              {t("common.cancel")}
            </button>
            <button
              className="button destructive"
              disabled={busy}
              onClick={() =>
                void run(
                  () =>
                    api(
                      `plants/${plant.id}/treatments/${confirm.id}?version=${plant._version}`,
                      { method: "DELETE" },
                    ),
                  t("treatment.stopped"),
                )
                  .then(() => setConfirm(null))
                  .catch((e) => setError(e.message))
              }
            >
              {t("treatment.stopConfirm")}
            </button>
          </div>
        </Modal>
      )}
    </section>
  );
}
