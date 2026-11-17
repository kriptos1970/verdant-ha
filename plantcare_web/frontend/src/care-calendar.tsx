import { useEffect, useState } from "react";
import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Leaf,
  MapPin,
  Play,
  Clock3,
  Pencil,
} from "lucide-react";
import type { Action, Plant, CareEvent } from "./types";
import { api } from "./api";
import { Avatar, eventIcon } from "./ui";
import { useI18n } from "./i18n";
import { useCareLabels } from "./care-labels";

export function dayKey(value: string, zone: string) {
  const parts = new Intl.DateTimeFormat("en", {
    timeZone: zone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date(value));
  const get = (key: string) => parts.find((p) => p.type === key)?.value;
  return `${get("year")}-${get("month")}-${get("day")}`;
}
const shift = (day: string, days: number) => {
  const date = new Date(day + "T12:00:00Z");
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
};
const display = (day: string, options: Intl.DateTimeFormatOptions, locale = "it") =>
  new Date(day + "T12:00:00Z").toLocaleDateString(locale, {
    ...options,
    timeZone: "UTC",
  });
function DayButton({
  day,
  selected,
  today,
  actions,
  onClick,
}: {
  day: string;
  selected?: boolean;
  today: string;
  actions: Action[];
  onClick: () => void;
}) {
  const { plural, locale } = useI18n();
  const dateText = display(day, { weekday: "long", day: "numeric", month: "long" }, locale);
  return (
    <button
      className={`calendar-day ${selected ? "selected" : ""} ${day === today ? "is-today" : ""}`}
      onClick={onClick}
      aria-pressed={Boolean(selected)}
      aria-label={plural("calendar.dayAria", actions.length, { date: dateText })}
    >
      <small>{display(day, { weekday: "short" }, locale)}</small>
      <strong>{Number(day.slice(-2))}</strong>
      <span className="day-dots" aria-hidden="true">
        {actions.slice(0, 3).map((a) => (
          <i
            key={a.id}
            className={
              a.kind === "Annaffia"
                ? "water"
                : a.kind === "Concima"
                  ? "feed"
                  : "other"
            }
          />
        ))}
      </span>
    </button>
  );
}
export function WeekStrip({
  actions,
  zone,
  onOpen,
}: {
  actions: Action[];
  zone: string;
  onOpen: () => void;
}) {
  const { t, locale } = useI18n();
  const today = dayKey(new Date().toISOString(), zone);
  return (
    <section className="panel native-week">
      <div className="section-heading">
        <div>
          <h2>{t("calendar.title")}</h2>
          <p>{t("calendar.subtitle")}</p>
        </div>
        <button className="button secondary" onClick={onOpen}>
          {t("calendar.open")}
        </button>
      </div>
      <div className="calendar-week">
        {Array.from({ length: 7 }, (_, i) => shift(today, i)).map((day) => (
          <DayButton
            key={day}
            day={day}
            today={today}
            selected={day === today}
            actions={actions.filter((a) => dayKey(a.dueDate, zone) === day)}
            onClick={onOpen}
          />
        ))}
      </div>
    </section>
  );
}
export function CareCalendar({
  plants,
  actions,
  room,
  setRoom,
  zone,
  onRound,
  onOpenPlant,
  onAction,
  onEditEvent,
}: {
  plants: Plant[];
  actions: Action[];
  room: string;
  setRoom: (room: string) => void;
  zone: string;
  onRound: () => void;
  onOpenPlant: (id: string) => void;
  onAction: (a: Action) => void;
  onEditEvent: (plant: Plant, event: CareEvent) => void;
}) {
  const { t, plural, locale } = useI18n();
  const { actionLabel, dueLabel, kindLabel } = useCareLabels();
  const today = dayKey(new Date().toISOString(), zone);
  const [mode, setMode] = useState("Calendario"),
    [selected, setSelected] = useState(today),
    [month, setMonth] = useState(false),
    [historyPlant, setHistoryPlant] = useState(""),
    [kind, setKind] = useState(""),
    [from, setFrom] = useState(""),
    [to, setTo] = useState("");
  const rooms = [...new Set(plants.map((p) => p.room))].sort((a, b) =>
    a.localeCompare(b, locale),
  );
  const filtered = actions.filter((a) => room === "Tutte" || a.room === room);
  const weekday = new Date(selected + "T12:00:00Z").getUTCDay();
  const monday = shift(selected, -((weekday + 6) % 7));
  const first = selected.slice(0, 7) + "-01";
  const monthWeekday = new Date(first + "T12:00:00Z").getUTCDay();
  const monthStart = shift(first, -((monthWeekday + 6) % 7));
  const days = Array.from({ length: month ? 42 : 7 }, (_, i) =>
    shift(month ? monthStart : monday, i),
  );
  const go = (direction: number) => {
    if (month) {
      const date = new Date(first + "T12:00:00Z");
      date.setUTCMonth(date.getUTCMonth() + direction);
      setSelected(date.toISOString().slice(0, 10));
    } else setSelected(shift(selected, direction * 7));
  };
  const selectedActions = filtered.filter(
    (a) => dayKey(a.dueDate, zone) === selected,
  );
  const oldActions = filtered.filter((a) => a.daysUntil < 0);
  type HistoryPage={items:{plantID:string;plantName:string;room:string;version:number;event:CareEvent}[];total:number;hasNextPage:boolean;kinds:string[]};
  const [historyPage,setHistoryPage]=useState(1),[historyData,setHistoryData]=useState<HistoryPage>(),[historyError,setHistoryError]=useState(''),[historyBusy,setHistoryBusy]=useState(false);
  const filterKey=JSON.stringify([room,historyPlant,kind,from,to]);
  const revision=plants.map(p=>`${p.id}:${p._version}`).join(',');
  const [appliedFilter,setAppliedFilter]=useState(filterKey);
  const currentPage=filterKey===appliedFilter?historyPage:1;
  useEffect(()=>{setAppliedFilter(filterKey);setHistoryPage(1)},[filterKey,revision]);
  useEffect(()=>{
    if(mode!=='Cronologia')return;
    let current=true;setHistoryBusy(true);setHistoryError('');setHistoryData(undefined);
    const params=new URLSearchParams({page:String(currentPage),limit:'50',room:room==='Tutte'?'':room,plant_id:historyPlant,kind,from_day:from,to_day:to});
    api<HistoryPage>(`history?${params}`).then(data=>{if(current)setHistoryData(data)}).catch(e=>{if(current)setHistoryError(e.message)}).finally(()=>{if(current)setHistoryBusy(false)});
    return()=>{current=false};
  },[mode,currentPage,filterKey,revision]);
  const history=(historyData?.items||[]).flatMap(row=>{
    const plant=plants.find(p=>p.id===row.plantID);
    return plant?[{plant:{...plant,_version:row.version},event:row.event}]:[];
  });
  const row = (a: Action) => {
    const plant = plants.find((p) => p.id === a.plantID);
    if (!plant) return null;
    const Icon = eventIcon(a.kind);
    return (
      <div className="care-row" key={a.id}>
        <button className="row-identity" onClick={() => onOpenPlant(plant.id)}>
          <Avatar plant={plant} />
          <span>
            <strong>{plant.name}</strong>
            <small>
              {plant.room} · {actionLabel(a)}
            </small>
            {a.reason && <small className="care-reason">{a.reason}</small>}
          </span>
        </button>
        <span className={`pill ${a.daysUntil < 0 ? "late" : ""}`}>
          {dueLabel(a.daysUntil)}
        </span>
        <button
          className="round-action"
          aria-label={`${actionLabel(a)}: ${plant.name}`}
          onClick={() => onAction(a)}
        >
          <Icon size={18} />
        </button>
      </div>
    );
  };
  return (
    <>
      <div className="care-mode-toolbar">
        <div className="segmented" aria-label={t("calendar.viewAria")}>
          {([["Calendario", "calendar.view.calendar"], ["Cronologia", "calendar.view.history"]] as const).map(([m, key]) => (
            <button
              key={m}
              className={mode === m ? "selected" : ""}
              aria-pressed={mode === m}
              onClick={() => setMode(m)}
            >
              {t(key)}
            </button>
          ))}
        </div>
        <button className="button primary" onClick={onRound}>
          <Play size={16} />
          {t("calendar.round")}
        </button>
      </div>
      <div className="chips">
        {["Tutte", ...rooms].map((r) => (
          <button
            key={r}
            className={room === r ? "selected" : ""}
            onClick={() => setRoom(r)}
          >
            {r === "Tutte" ? t("calendar.allRooms") : r}
          </button>
        ))}
      </div>
      {mode === "Calendario" ? (
        <>
          <section className="panel calendar-panel">
            <div className="section-heading">
              <div>
                <h2>{display(selected, { month: "long", year: "numeric" }, locale)}</h2>
                <p className="muted small-text">{t("calendar.pickDay")}</p>
              </div>
              <div className="button-row">
                <button
                  className="text-button"
                  onClick={() => setSelected(today)}
                >
                  {t("calendar.today")}
                </button>
                <button
                  className="icon-button"
                  aria-label={month ? t("calendar.closeMonth") : t("calendar.monthAria")}
                  aria-pressed={month}
                  onClick={() => setMonth(!month)}
                >
                  <CalendarDays size={19} /><span className="ios-control-label">{month ? t("calendar.week") : t("calendar.month")}</span>
                </button>
              </div>
            </div>
            <div className="calendar-navigation">
              <button
                className="icon-button"
                aria-label={month ? t("calendar.prevMonth") : t("calendar.prevWeek")}
                onClick={() => go(-1)}
              >
                <ChevronLeft size={18} />
              </button>
              <span>{month ? t("calendar.month") : t("calendar.week")}</span>
              <button
                className="icon-button"
                aria-label={month ? t("calendar.nextMonth") : t("calendar.nextWeek")}
                onClick={() => go(1)}
              >
                <ChevronRight size={18} />
              </button>
            </div>
            <div className={month ? "calendar-month" : "calendar-week"}>
              {days.map((day) => (
                <DayButton
                  key={day}
                  day={day}
                  today={today}
                  selected={day === selected}
                  actions={filtered.filter(
                    (a) => dayKey(a.dueDate, zone) === day,
                  )}
                  onClick={() => setSelected(day)}
                />
              ))}
            </div>
          </section>
          <section className="panel">
            <div className="section-heading">
              <h2>
                {display(selected, {
                  weekday: "long",
                  day: "numeric",
                  month: "long",
                }, locale)}
                <span>{selectedActions.length}</span>
              </h2>
            </div>
            {selectedActions.length ? (
              selectedActions.map(row)
            ) : (
              <div className="gentle-empty">
                <Leaf size={25} />
                <div>
                  <strong>{t("calendar.noActions")}</strong>
                  <p>{t("calendar.noActionsText")}</p>
                </div>
              </div>
            )}
          </section>
          {oldActions.length > 0 && (
            <details className="panel overdue-panel">
              <summary>
                <Clock3 size={17} />
                {plural("calendar.older", oldActions.length)}
              </summary>
              {oldActions.map(row)}
            </details>
          )}
        </>
      ) : (
        <section className="panel">
          <h2>{t("calendar.historyTitle")}</h2>
          <div className="history-filters">
            <label>
              {t("calendar.plantFilter")}
              <select
                value={historyPlant}
                onChange={(e) => setHistoryPlant(e.target.value)}
              >
                <option value="">{t("calendar.allPlants")}</option>
                {plants.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              {t("calendar.typeFilter")}
              <select value={kind} onChange={(e) => setKind(e.target.value)}>
                <option value="">{t("calendar.allCare")}</option>
                {(historyData?.kinds || [])
                  .sort()
                  .map((k) => (
                    <option key={k}>{k}</option>
                  ))}
              </select>
            </label>
            <label>
              {t("calendar.from")}
              <input
                type="date"
                value={from}
                onChange={(e) => setFrom(e.target.value)}
              />
            </label>
            <label>
              {t("calendar.to")}
              <input
                type="date"
                min={from}
                value={to}
                onChange={(e) => setTo(e.target.value)}
              />
            </label>
          </div>
          {historyBusy&&<p role="status">{t("calendar.loading")}</p>}
          {historyError&&<p role="alert">{historyError}</p>}
          {historyData&&<p className="muted small-text">{t("calendar.count", { total: historyData.total, page: currentPage })}</p>}
          {history.map(({ plant, event }) => {
            const Icon = eventIcon(event.kind);
            return (
              <div className="global-history-event" key={plant.id + event.id}>
                <span className="timeline-icon">
                  <Icon size={17} />
                </span>
                <div>
                  <button
                    className="text-button history-plant-link"
                    onClick={() => onOpenPlant(plant.id)}
                  >
                    {plant.name}
                    <ChevronRight size={12} />
                  </button>
                  <strong>
                    {kindLabel(event.kind)}
                    {event.status === "postponed" ? ` · ${t("calendar.postponed")}` : ""}
                  </strong>
                  <small>
                    <MapPin size={11} />
                    {plant.room} ·{" "}
                    {new Date(event.date).toLocaleString(locale, {
                      timeZone: zone,
                      dateStyle: "medium",
                      timeStyle: "short",
                    })}
                  </small>
                  {event.note && <p className="preserve">{event.note}</p>}
                </div>
                <button
                  className="icon-button"
                  aria-label={t("calendar.editAria", { kind: kindLabel(event.kind), name: plant.name })}
                  onClick={() => onEditEvent(plant, event)}
                >
                  <Pencil size={15} />
                </button>
              </div>
            );
          })}
          {historyData&&<nav className="button-row" aria-label={t("calendar.pagesAria")}><button className="button secondary" disabled={historyBusy||currentPage===1} onClick={()=>setHistoryPage(p=>p-1)}>{t("calendar.prevPage")}</button><button className="button secondary" disabled={historyBusy||!historyData.hasNextPage} onClick={()=>setHistoryPage(p=>p+1)}>{t("calendar.nextPage")}</button></nav>}
          {!historyBusy&&!historyError&&historyData&&!history.length && (
            <div className="gentle-empty">
              <CalendarDays size={24} />
              <p>{t("calendar.empty")}</p>
            </div>
          )}
        </section>
      )}
    </>
  );
}
