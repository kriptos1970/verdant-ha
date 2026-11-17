import {healthSymptoms,healthAreas,healthCheckNote} from "./care-notes";
import {IOSIcon,iosNavigation,iosTools} from "./ios-icons";
import React, { useState, useEffect, useCallback, useRef } from "react";
import { createRoot } from "react-dom/client";
import {
  Leaf,
  House,
  CalendarDays,
  FlaskConical,
  Ellipsis,
  Plus,
  Search,
  ArrowUpRight,
  ArrowLeft,
  X,
  Droplets,
  Sun,
  Sprout,
  ChevronRight,
  ChevronLeft,
  Check,
  Pencil,
  Trash2,
  Upload,
  Download,
  Settings2,
  Sparkles,
  Thermometer,
  Camera,
  BookOpen,
  BarChart3,
  RotateCw,
  Flower2,
  Menu,
  MapPin,
  ShieldCheck,
  AlertCircle,
  LoaderCircle,
  ImagePlus,
  CheckCircle2,
  CircleHelp,
} from "lucide-react";
import type {
  Plant,
  Product,
  Action,
  Settings,
  Proposal,
  Sensor,
  Mapping,
  Measure,
  Growth,
  CareSelection,
  Treatment,
} from "./types";
import { api, photoURL, uid, todayISO } from "./api";
import "./style.css";
import "./ios-layout.css";
import {IOSProducts,IOSPlantOverview,useIOSLayout} from "./ios-layout";
import { PlantAssistant, AIModelCatalog } from "./ai-assistant";
import { AdaptiveEditor, CareInsights } from "./adaptive";
import { Avatar, ProductPhoto, Modal, eventIcon } from "./ui";
import { CareRound } from "./care-round";
import { TreatmentEditor, TreatmentPanel } from "./treatments";
import { HealthAlbum, HealthPhotoEditor } from "./health-album";
import { PlantLabel, LabelsTool } from "./plant-labels";
import { routePlant } from "./plant-links";
import { ActionGuide, PlantKnowledge, GuidesTool, DiagnosisTool } from "./health-guides";
import { SpeciesCatalog } from "./species-catalog";
import { IdentificationTool, SpeciesLibrary, BotanicalLookup, type PlantSeed } from "./knowledge";
import { CareCalendar, WeekStrip } from "./care-calendar";
import { I18nProvider, useI18n, type MessageKey, type LanguagePreference } from "./i18n";
import { useCareLabels } from "./care-labels";

type Page = "today" | "plants" | "care" | "products" | "more" | "analytics";
const navigation = [
  { id: "today", labelKey: "nav.today", icon: House },
  { id: "plants", labelKey: "nav.plants", icon: Leaf },
  { id: "care", labelKey: "nav.care", icon: CalendarDays },
  { id: "products", labelKey: "nav.products", icon: FlaskConical },
  { id: "more", labelKey: "nav.more", icon: Ellipsis },
] as const;
const pageTitleKeys: Record<Page, MessageKey> = {
  today: "page.overview",
  plants: "page.plants",
  care: "page.care",
  products: "page.products",
  more: "page.tools",
  analytics: "page.analytics",
};
const toolDefinitions = [
  { id: "identify", titleKey: "tools.identify.title", descKey: "tools.identify.desc", icon: Camera },
  { id: "catalog", titleKey: "tools.catalog.title", descKey: "tools.catalog.desc", icon: BookOpen },
  { id: "labels", titleKey: "tools.labels.title", descKey: "tools.labels.desc", icon: Leaf },
  { id: "guides", titleKey: "tools.guides.title", descKey: "tools.guides.desc", icon: BookOpen },
  { id: "diagnosis", titleKey: "tools.diagnosis.title", descKey: "tools.diagnosis.desc", icon: ShieldCheck },
  { id: "ai", titleKey: "tools.ai.title", descKey: "tools.ai.desc", icon: Sparkles },
  { id: "species", titleKey: "tools.species.title", descKey: "tools.species.desc", icon: BookOpen },
  { id: "sensors", titleKey: "tools.sensors.title", descKey: "tools.sensors.desc", icon: Thermometer },
  { id: "backup", titleKey: "tools.backup.title", descKey: "tools.backup.desc", icon: Upload },
  { id: "settings", titleKey: "tools.settings.title", descKey: "tools.settings.desc", icon: Settings2 },
] as const;
const categories = ["Tropicale", "Succulenta", "Aromatica", "Fiorita", "Altro"];
const kinds = [
  "Annaffia",
  "Concima",
  "Ruota",
  "Rinvasa",
  "Pota",
  "Controlla salute",
  "Aggiorna progressi",
  "Trattamento",
];
const detailTabs = [
  { id: "Scheda", key: "detail.tabs.sheet" },
  { id: "Guida", key: "detail.tabs.guide" },
  { id: "Salute", key: "detail.tabs.health" },
  { id: "Diario", key: "detail.tabs.diary" },
  { id: "Trattamenti", key: "detail.tabs.treatments" },
  { id: "Misure", key: "detail.tabs.measures" },
  { id: "AI", key: "detail.tabs.ai" },
] as const;
const healthStates = ["Eccellente", "Buona", "In difficoltà", "Malata"] as const;
const healthStateKeys: Record<string, MessageKey> = {
  Eccellente: "health.state.excellent",
  Buona: "health.state.good",
  "In difficoltà": "health.state.struggling",
  Malata: "health.state.sick",
};
const symptomKeys: Record<string, MessageKey> = {
  "Foglie gialle": "health.symptom.yellowLeaves",
  "Punte secche": "health.symptom.dryTips",
  "Foglie cadenti": "health.symptom.droopingLeaves",
  Macchie: "health.symptom.spots",
  Parassiti: "health.symptom.pests",
  "Crescita lenta": "health.symptom.slowGrowth",
};
const areaKeys: Record<string, MessageKey> = {
  Foglie: "health.area.leaves",
  "Retro foglie": "health.area.leafUnderside",
  Fusto: "health.area.stem",
  Terreno: "health.area.soil",
  Radici: "health.area.roots",
  Drenaggio: "health.area.drainage",
};
const planModeKeys: Record<string, MessageKey> = {
  Manuale: "detail.planMode.manual",
  Intelligente: "detail.planMode.smart",
  AI: "detail.planMode.ai",
};
function Botanical({ small = false }: { small?: boolean }) {
  return (
    <div className={`botanical ${small ? "small" : ""}`} aria-hidden="true">
      <div className="stem" />
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <i key={i} className={`leaf leaf-${i}`} />
      ))}
      <div className="pot" />
    </div>
  );
}
function App() {
  const { t } = useI18n();
  const { actionLabel, dueLabel } = useCareLabels();
  const [page, setPage] = useState<Page>("today"),
    [plants, setPlants] = useState<Plant[]>([]),
    [products, setProducts] = useState<Product[]>([]),
    [settings, setSettings] = useState<Settings>(),
    [proposals, setProposals] = useState<Proposal[]>([]),
    [selected, setSelected] = useState<string | null>(
      new URLSearchParams(location.hash.slice(1)).get("plant"),
    );
  const [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false),
    [search, setSearch] = useState(""),
    [room, setRoom] = useState("Tutte"),
    [filter, setFilter] = useState("Tutte"),
    [menu, setMenu] = useState(false);
  const [plantEditor, setPlantEditor] = useState<Plant | "new" | null>(null),
    [productEditor, setProductEditor] = useState<Product | "new" | null>(null),
    [action, setAction] = useState<CareSelection | null>(null),
    [roundOpen, setRoundOpen] = useState(false),
    [cycleProduct, setCycleProduct] = useState<Product | null>(null),
    [confirm, setConfirm] = useState<{
      title: string;
      run: () => Promise<void>;
    } | null>(null),
    [tool, setTool] = useState<string | null>(null);
  const phoneLayout=useIOSLayout();
  const [phoneCollectionMode,setPhoneCollectionMode]=useState("Piante");
  const [plantSeed,setPlantSeed]=useState<PlantSeed>();
  const preparePlant=(seed:PlantSeed)=>{setPlantSeed(seed);setPlantEditor("new")};
  const reload = useCallback(async () => {
    const [p, f, s, a] = await Promise.all([
      api<Plant[]>("plants?summary=true"),
      api<Product[]>("fertilizers"),
      api<Settings>("settings"),
      api<Proposal[]>("proposals"),
    ]);
    setPlants(p);
    setProducts(f);
    setSettings(s);
    setProposals(a);
  }, []);
  useEffect(() => {
    reload()
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [reload]);
  useEffect(() => {
    const refresh = () => {
      if (document.visibilityState === "visible")
        void reload().catch((e) => setError(e.message));
    };
    const timer = setInterval(refresh, 60000);
    document.addEventListener("visibilitychange", refresh);
    return () => {
      clearInterval(timer);
      document.removeEventListener("visibilitychange", refresh);
    };
  }, [reload]);
  useEffect(() => {
    if (!notice) return;
    const t = setTimeout(() => setNotice(""), 5000);
    return () => clearTimeout(t);
  }, [notice]);
  useEffect(() => {
    const onHash = () =>
      setSelected(new URLSearchParams(location.hash.slice(1)).get("plant"));
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  useEffect(()=>{
    if(window.parent===window)return;
    const properties=(event:MessageEvent)=>{if(event.source!==window.parent||event.origin!==location.origin||event.data?.type!=="home-assistant/properties")return;const id=routePlant(event.data.route?.path);if(id){setSelected(id);location.hash=`plant=${id}`}};
    window.addEventListener("message",properties);
    window.parent.postMessage({type:"home-assistant/subscribe-properties"},location.origin);
    return()=>{window.removeEventListener("message",properties);window.parent.postMessage({type:"home-assistant/unsubscribe-properties"},location.origin)};
  },[]);
  const run = async (fn: () => Promise<unknown>, message = "Salvato") => {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await fn();
      await reload();
      if (message) setNotice(message);
    } catch (e) {
      setError((e as Error).message);
      throw e;
    } finally {
      setBusy(false);
    }
  };
  const safeRun = (fn: () => Promise<unknown>, message?: string) => {
    void run(fn, message).catch(() => {});
  };
  const rooms = [...new Set(plants.map((p) => p.room))].sort();
  const allActions = plants
    .flatMap((p) => p._actions)
    .sort((a, b) => a.dueDate.localeCompare(b.dueDate));
  const due = allActions.filter((a) => a.daysUntil === 0),
    week = allActions.filter((a) => a.daysUntil >= 0 && a.daysUntil <= 7);
  const filtered = plants.filter(
    (p) =>
      (room === "Tutte" || p.room === room) &&
      `${p.name} ${p.species} ${p.room}`
        .toLowerCase()
        .includes(search.toLowerCase()) &&
      (filter === "Tutte" ||
        (filter === "Da curare" && p._actions.some((a) => a.daysUntil === 0)) ||
        (filter === "Rischio animali" &&
          p.safetyProfile?.poisonousToPets === true)),
  );
  const [detailPlant,setDetailPlant]=useState<Plant>();
  const [detailError,setDetailError]=useState(''),[detailRetry,setDetailRetry]=useState(0);
  const selectedSummary=plants.find(p=>p.id===selected);
  useEffect(()=>{
    let current=true;setDetailPlant(undefined);setDetailError('');
    if(selectedSummary)api<Plant>(`plants/${selectedSummary.id}`).then(p=>{if(current)setDetailPlant(p)}).catch(e=>{if(current)setDetailError(e.message)});
    return()=>{current=false};
  },[selectedSummary?.id,selectedSummary?._version,detailRetry]);
  const selectedPlant=detailPlant?.id===selectedSummary?.id&&detailPlant?._version===selectedSummary?._version?detailPlant:undefined;
  const openPlant = (id: string | null) => {
    setSelected(id);
    history.replaceState(
      null,
      "",
      id
        ? `#plant=${encodeURIComponent(id)}`
        : location.pathname + location.search,
    );
  };
  const navigate = (p: Page) => {
    setPage(p);
    openPlant(null);
    setMenu(false);
    setSearch("");
    setRoom("Tutte");
  };
  const row = (a: Action) => {
    const plant = plants.find((p) => p.id === a.plantID)!;
    const Icon = eventIcon(a.kind);
    return (
      <div className="care-row" key={a.id}>
        <button className="row-identity" onClick={() => openPlant(plant.id)}>
          <Avatar plant={plant} />
          <span>
            <strong>{plant.name}</strong>
            <small>
              {plant.room} · {actionLabel(a)}
              {a.reason && <span className="care-reason">{a.reason}</span>}
            </small>
          </span>
        </button>
        <span className={`pill ${a.daysUntil < 0 ? "late" : ""}`}>
          {dueLabel(a.daysUntil)}
        </span>
        <button
          className="round-action"
          disabled={busy}
          onClick={() => setAction({ plant, kind: a.kind, scheduled: a })}
          aria-label={`${a.kind}: ${plant.name}`}
        >
          <Icon size={18} />
        </button>
      </div>
    );
  };
  const activeTool = tool ? toolDefinitions.find((item) => item.id === tool) : undefined;
  const pageTitle = page === "plants"
    ? (room === "Tutte" ? t("page.allPlants") : room)
    : page === "more"
      ? (activeTool ? t(activeTool.titleKey) : t("page.tools"))
      : t(pageTitleKeys[page]);
  return (
    <div
      className={`app ${settings?.ingress && window.parent!==window ? "in-ha" : ""} ${selectedSummary ? "has-detail" : ""} ${["today", "plants", "care"].includes(page) ? "native-split" : ""}`}
    >
      <aside className={`sidebar ${menu ? "open" : ""}`}>
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            navigate("today");
          }}
        >
          <div className="brand-mark">
            <Leaf size={24} />
          </div>
          <span>
            PlantCare<small>{t("app.brandTagline")}</small>
          </span>
        </a>
        <div className="sidebar-label">{t("app.collection")}</div>
        <nav>
          {navigation.map((item) => (
            <button
              key={item.id}
              className={page === item.id ? "active" : ""}
              onClick={() => navigate(item.id)}
            >
              <item.icon size={19} />
              {t(item.labelKey)}
              {item.id === "care" && due.length > 0 && <b>{due.length}</b>}
            </button>
          ))}
          <button
            className={page === "analytics" ? "active" : ""}
            onClick={() => navigate("analytics")}
          >
            <BarChart3 size={19} />
            {t("nav.analytics")}
          </button>
        </nav>
        <div className="sidebar-label rooms-label">
          {t("app.environments")} <span>{rooms.length}</span>
        </div>
        <nav className="rooms">
          {rooms.map((r) => (
            <button
              key={r}
              className={page === "plants" && room === r ? "active" : ""}
              onClick={() => {
                setPage("plants");
                setRoom(r);
                openPlant(null);
                setMenu(false);
              }}
            >
              <MapPin size={16} />
              {r}
              <small>{plants.filter((p) => p.room === r).length}</small>
            </button>
          ))}
          {rooms.length === 0 && (
            <p className="muted sidebar-empty">
              {t("app.emptyRooms")}
            </p>
          )}
        </nav>
        <div className="sidebar-bottom">
          <span className="connection-dot" />
          <div>
            Home Assistant
            <small>{t("app.localArchive")} · {settings?.version || "…"}</small>
          </div>
          <button
            className="icon-button"
            aria-label={t("app.settingsAria")}
            onClick={() => {
              navigate("more");
              setTool("settings");
            }}
          >
            <Settings2 size={18} />
          </button>
        </div>
      </aside>
      {menu && (
        <button
          className="sidebar-scrim"
          aria-label={t("app.closeMenu")}
          onClick={() => setMenu(false)}
        />
      )}
      <main data-page={page} data-collection-mode={phoneCollectionMode} data-tool={tool||""}>
        <header className="topbar">
          <button
            className="icon-button mobile-menu"
            aria-label={t("app.openMenu")}
            onClick={() => setMenu(true)}
          >
            <Menu size={21} />
          </button>
          <div className="breadcrumb">
            {t("app.breadcrumb")} <ChevronRight size={14} />
            <strong>
              {page === "analytics" ? t("nav.analytics") : t(navigation.find((n) => n.id === page)?.labelKey ?? "nav.more")}
            </strong>
          </div>
          <div className="topbar-right">
            <span className="local-badge">
              <span className="connection-dot" /> {t("app.localArchive")}
            </span>
            <button
              className="button primary compact"
              aria-label={page === "products" ? t("app.newProduct") : t("app.newPlant")}
              onClick={() =>
                page === "products"
                  ? setProductEditor("new")
                  : setPlantEditor("new")
              }
            >
              <Plus size={17} />
              <span>
                {page === "products" ? t("app.newProduct") : t("app.newPlant")}
              </span>
            </button>
          </div>
        </header>
        <div className="content">
          {page==="more"&&tool&&<button className="ios-tool-back text-button" onClick={()=>setTool(null)}><ArrowLeft size={19}/>{t("app.toolsBack")}</button>}
          <h1 className="ios-page-title">{pageTitle}</h1>
          <div aria-live="polite">
            {error && (
              <div className="alert error">
                <AlertCircle size={18} />
                <span>{error}</span>
                <button
                  className="icon-button"
                  onClick={() => setError("")}
                  aria-label={t("app.errorClose")}
                >
                  <X size={16} />
                </button>
              </div>
            )}
          </div>
          {loading ? (
            <div className="loading">
              <LoaderCircle className="spin" />
              {t("app.loading")}
            </div>
          ) : (
            <>
              {page === "today" && (
                <>
                  <div className="page-heading">
                    <div>
                      <div className="eyebrow">
                        {new Date().toLocaleDateString("it-IT", {
                          weekday: "long",
                          day: "numeric",
                          month: "long",
                        })}
                      </div>
                      <h1>
                        {new Date().getHours() < 12
                          ? "Buongiorno"
                          : new Date().getHours() < 18
                            ? "Buon pomeriggio"
                            : "Buonasera"}{" "}
                        <span aria-hidden="true">🌿</span>
                      </h1>
                      <p>Ecco come stanno le tue piante oggi.</p>
                    </div>
                    <span className="heading-icon">
                      <Sun size={28} />
                    </span>
                  </div>
                  <WeekStrip
                    actions={allActions}
                    zone={settings?.timezone || "Europe/Rome"}
                    onOpen={() => setPage("care")}
                  />
                  <section className="hero">
                    <div>
                      <span className="eyebrow">IL TUO GIARDINO OGGI</span>
                      <h2>
                        {plants.length === 0
                          ? "Tutto comincia con una pianta."
                          : due.length > 0
                            ? "Le tue piante ti aspettano."
                            : "Il giardino è in ordine"}
                      </h2>
                      <p>
                        {plants.length === 0
                          ? "Aggiungi la prima pianta o porta qui la tua collezione PlantCare."
                          : due.length > 0
                            ? `${due.length} attività da completare. Prendiamocene cura, una alla volta.`
                            : "Nessuna cura in scadenza oggi. È un buon momento per osservare come crescono."}
                      </p>
                      <button
                        className="button hero-button"
                        onClick={() =>
                          plants.length
                            ? due.length
                              ? setRoundOpen(true)
                              : setPage("care")
                            : setPlantEditor("new")
                        }
                      >
                        {plants.length
                          ? due.length
                            ? "Apri il giro di cura"
                            : "Vedi il calendario"
                          : "Aggiungi una pianta"}
                        <ArrowUpRight size={17} />
                      </button>
                    </div>
                    <Botanical />
                  </section>
                  <div className="stats">
                    <div>
                      <span>
                        <Leaf size={18} />
                        La collezione
                      </span>
                      <strong>
                        {plants.length}
                        <small>
                          {plants.length === 1 ? "pianta" : "piante"}
                        </small>
                      </strong>
                    </div>
                    <div>
                      <span>
                        <Droplets size={18} />
                        Da fare oggi
                      </span>
                      <strong>
                        {due.length}
                        <small>{due.length === 1 ? "cura" : "cure"}</small>
                      </strong>
                    </div>
                    <div>
                      <span>
                        <CalendarDays size={18} />
                        Questa settimana
                      </span>
                      <strong>
                        {week.length}
                        <small>attività</small>
                      </strong>
                    </div>
                  </div>
                  <section className="panel">
                    <div className="section-heading">
                      <h2>
                        Un’attenzione per oggi <span>{due.length}</span>
                      </h2>
                      <button
                        className="text-button"
                        onClick={() => setPage("care")}
                      >
                        Tutte le cure <ChevronRight size={16} />
                      </button>
                    </div>
                    {due.length ? (
                      due.slice(0, 5).map(row)
                    ) : (
                      <div className="gentle-empty">
                        <CheckCircle2 size={28} />
                        <div>
                          <strong>
                            {plants.length
                              ? "Tutto in ordine per oggi"
                              : "Il tuo calendario prenderà vita qui"}
                          </strong>
                          <p>
                            {plants.length
                              ? "Le prossime attività compariranno al momento giusto."
                              : "Le cure appariranno dopo aver aggiunto le piante."}
                          </p>
                        </div>
                      </div>
                    )}
                  </section>
                  {proposals.length > 0 && (
                    <section className="ai-banner">
                      <Sparkles size={22} />
                      <div>
                        <strong>
                          {proposals.length} proposte per i tuoi piani AI
                        </strong>
                        <p>Leggi le motivazioni prima di applicarle.</p>
                      </div>
                      <button
                        className="text-button"
                        onClick={() => {
                          setPage("more");
                          setTool("ai");
                        }}
                      >
                        Esamina <ChevronRight size={17} />
                      </button>
                    </section>
                  )}
                  <div className="section-heading collection-heading">
                    <h2>Le tue piante</h2>
                    <button
                      className="text-button"
                      onClick={() => setPage("plants")}
                    >
                      La collezione <ChevronRight size={16} />
                    </button>
                  </div>
                  {plants.length ? (
                    <div className="plant-grid">
                      {plants.slice(0, 6).map((p) => (
                        <PlantCard
                          key={p.id}
                          plant={p}
                          onClick={() => openPlant(p.id)}
                        />
                      ))}
                    </div>
                  ) : (
                    <EmptyCollection
                      onAdd={() => setPlantEditor("new")}
                      onImport={() => {
                        navigate("more");
                        setTool("backup");
                      }}
                    />
                  )}
                </>
              )}
              {page === "plants" && (
                <>
                  <div className="page-heading">
                    <div>
                      <div className="eyebrow">OGNI PIANTA, UNA STORIA</div>
                      <h1>{room === "Tutte" ? "Le tue piante" : room}</h1>
                      <p>
                        {plants.length} piante · {rooms.length} ambienti
                      </p>
                    </div>
                    <Leaf className="muted" size={30} />
                  </div>
                  <div className="collection-toolbar">
                    <label className="search">
                      <Search size={18} />
                      <input
                        aria-label="Cerca una pianta"
                        placeholder="Cerca nome, specie o ambiente"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                      />
                    </label>
                    <select
                      aria-label="Filtra per ambiente"
                      value={room}
                      onChange={(e) => setRoom(e.target.value)}
                    >
                      <option>Tutte</option>
                      {rooms.map((r) => (
                        <option key={r}>{r}</option>
                      ))}
                    </select>
                  </div>
                  <div className="ios-collection-controls"><div className="segmented">{["Piante","Ambienti"].map(m=><button key={m} aria-pressed={phoneCollectionMode===m} className={phoneCollectionMode===m?"selected":""} onClick={()=>setPhoneCollectionMode(m)}>{m}</button>)}</div><select aria-label="Filtra piante" value={filter} onChange={e=>setFilter(e.target.value)}>{["Tutte","Da curare","Rischio animali"].map(f=><option key={f}>{f}</option>)}</select></div>
                  {phoneCollectionMode==="Ambienti"&&<div className="ios-rooms">{rooms.filter(r=>!search||r.toLocaleLowerCase().includes(search.toLocaleLowerCase())).map(r=><button key={r} onClick={()=>{setRoom(r);setPhoneCollectionMode("Piante")}}><MapPin size={30}/><span><strong>{r}</strong><small>{plants.filter(p=>p.room===r).length} {plants.filter(p=>p.room===r).length===1?"pianta":"piante"}</small></span><ChevronRight size={20}/></button>)}</div>}
                  <div className="chips">
                    {["Tutte", "Da curare", "Rischio animali"].map((f) => (
                      <button
                        key={f}
                        className={filter === f ? "selected" : ""}
                        onClick={() => setFilter(f)}
                      >
                        {f}
                      </button>
                    ))}
                  </div>
                  {filtered.length ? (
                    <div className="plant-grid">
                      {(phoneLayout?[...filtered].sort((a,b)=>a.name.localeCompare(b.name,"it")):filtered).map((p) => (
                        <PlantCard
                          key={p.id}
                          plant={p}
                          onClick={() => openPlant(p.id)}
                        />
                      ))}
                    </div>
                  ) : plants.length ? (
                    <div className="empty-state">
                      <Search />
                      <h2>Nessuna pianta trovata</h2>
                      <p>Prova un altro nome o modifica i filtri.</p>
                    </div>
                  ) : (
                    <EmptyCollection
                      onAdd={() => setPlantEditor("new")}
                      onImport={() => {
                        navigate("more");
                        setTool("backup");
                      }}
                    />
                  )}
                </>
              )}
              {page === "care" && (
                <>
                  <div className="page-heading">
                    <div>
                      <div className="eyebrow">{t("care.pageEyebrow")}</div>
                      <h1>{t("care.pageTitle")}</h1>
                      <p>{t("care.pageSubtitle")}</p>
                    </div>
                    <CalendarDays size={30} className="muted" />
                  </div>
                  <CareCalendar
                    plants={plants}
                    actions={allActions}
                    room={room}
                    setRoom={setRoom}
                    zone={settings?.timezone || "Europe/Rome"}
                    onRound={() => setRoundOpen(true)}
                    onOpenPlant={openPlant}
                    onAction={(a) => {
                      const plant = plants.find((p) => p.id === a.plantID);
                      if (plant)
                        setAction({ plant, kind: a.kind, scheduled: a });
                    }}
                    onEditEvent={(plant, event) =>
                      setAction({ plant, kind: event.kind, event })
                    }
                  />
                </>
              )}
              {page === "products" && (
                <>
                  <div className="page-heading">
                    <div>
                      <div className="eyebrow">
                        QUELLO CHE SERVE AL TUO VERDE
                      </div>
                      <h1>Prodotti e fertilizzanti</h1>
                      <p>
                        Indicazioni, frequenze e note sempre a portata di mano.
                      </p>
                    </div>
                    <FlaskConical size={30} className="muted" />
                  </div>
                  <IOSProducts products={products} onEdit={setProductEditor} onCycle={setCycleProduct} onDelete={p=>setConfirm({title:`Eliminare ${p.name}?`,run:async()=>{await run(()=>api(`fertilizers/${p.id}?version=${p._version}`,{method:"DELETE"}),"Prodotto eliminato");setConfirm(null)}})}/>
                  {products.length ? (
                    <div className="product-grid">
                      {products.map((p) => (
                        <section className="panel product" key={p.id}>
                          <ProductPhoto product={p}/>
                          <h2>{p.name}</h2>
                          <p>{p.brand || "Marca non indicata"}</p>
                          {p.applicationIntervalDays && (
                            <span className="pill">
                              Ogni {p.applicationIntervalDays} giorni
                            </span>
                          )}
                          <p className="product-notes">
                            {p.dosage && (
                              <strong className="product-dose">
                                Dose: {p.dosage}
                              </strong>
                            )}
                            {p.notes || "Nessuna nota."}
                          </p>
                          <div className="button-row">
                            <button
                              className="button primary"
                              disabled={!plants.length}
                              onClick={() => setCycleProduct(p)}
                            >
                              <CalendarDays size={15} />
                              Pianifica ciclo
                            </button>
                            <button
                              className="button secondary"
                              onClick={() => setProductEditor(p)}
                            >
                              <Pencil size={15} />
                              Modifica
                            </button>
                            <button
                              className="icon-button danger"
                              aria-label={`Elimina ${p.name}`}
                              onClick={() =>
                                setConfirm({
                                  title: `Eliminare ${p.name}?`,
                                  run: async () => {
                                    await run(
                                      () =>
                                        api(
                                          `fertilizers/${p.id}?version=${p._version}`,
                                          { method: "DELETE" },
                                        ),
                                      "Prodotto eliminato",
                                    );
                                  },
                                })
                              }
                            >
                              <Trash2 size={17} />
                            </button>
                          </div>
                        </section>
                      ))}
                    </div>
                  ) : (
                    <div className="empty-state">
                      <FlaskConical />
                      <h2>Il tuo scaffale dei prodotti</h2>
                      <p>
                        Aggiungi fertilizzanti e annota le indicazioni del
                        produttore.
                      </p>
                      <button
                        className="button primary"
                        onClick={() => setProductEditor("new")}
                      >
                        <Plus size={17} />
                        Nuovo prodotto
                      </button>
                    </div>
                  )}
                </>
              )}
              {page === "analytics" && (
                <>
                  <div className="page-heading">
                    <div>
                      <div className="eyebrow">UNO SGUARDO D’INSIEME</div>
                      <h1>Come cresce il tuo giardino</h1>
                      <p>La collezione e le cure che hai registrato.</p>
                    </div>
                  </div>
                  <div className="stats">
                    <div>
                      <span>Piante</span>
                      <strong>{plants.length}</strong>
                    </div>
                    <div>
                      <span>Cure registrate</span>
                      <strong>
                        {plants.reduce(
                          (n, p) =>
                            n +
                            (p._careCount ?? p.history.filter(
                              (e) => !e.deletedAt && e.status !== "postponed",
                            ).length),
                          0,
                        )}
                      </strong>
                    </div>
                    <div>
                      <span>Ambienti</span>
                      <strong>{rooms.length}</strong>
                    </div>
                  </div>
                  <section className="panel">
                    <h2>Le piante per ambiente</h2>
                    {rooms.length ? (
                      rooms.map((r) => (
                        <div className="bar-row" key={r}>
                          <span>{r}</span>
                          <div>
                            <i
                              style={{
                                width: `${(plants.filter((p) => p.room === r).length / plants.length) * 100}%`,
                              }}
                            />
                          </div>
                          <strong>
                            {plants.filter((p) => p.room === r).length}
                          </strong>
                        </div>
                      ))
                    ) : (
                      <p className="muted">
                        Aggiungi le prime piante per iniziare.
                      </p>
                    )}
                  </section>
                </>
              )}
              {page === "more" && (
                <>
                  <div className="page-heading">
                    <div>
                      <div className="eyebrow">
                        {t("app.moreEyebrow")}
                      </div>
                      <h1>{t("app.moreTitle")}</h1>
                      <p>{t("app.moreSubtitle")}</p>
                    </div>
                  </div>
                  <div className="tools-grid">
                    {toolDefinitions.map((toolItem) => (
                      <React.Fragment key={toolItem.id}>
                      {toolItem.id==="identify"&&<h2 className="ios-tool-group ios-discover">{t("tools.group.discover")}</h2>}
                      {toolItem.id==="labels"&&<h2 className="ios-tool-group ios-assistance">{t("tools.group.assistance")}</h2>}
                      {toolItem.id==="ai"&&<h2 className="ios-tool-group ios-manage">{t("tools.group.management")}</h2>}
                      <button
                        data-tool={toolItem.id}
                        className={`tool-card ${tool === toolItem.id ? "selected" : ""}`}
                        key={toolItem.id}
                        onClick={() => setTool(toolItem.id)}
                      >
                        <span>
                          <toolItem.icon size={23} className="desktop-symbol"/><IOSIcon name={iosTools[toolItem.id]} size={23} className="mobile-symbol"/>
                        </span>
                        <div>
                          <strong>{t(toolItem.titleKey)}</strong>
                          <small>{t(toolItem.descKey)}</small>
                        </div>
                        <ChevronRight size={18} />
                      </button>
                      </React.Fragment>
                    ))}
                  </div>
                  {tool === "labels" && <LabelsTool plants={plants} settings={settings} onOpen={openPlant}/>}
                  {tool === "guides" && <GuidesTool plants={plants}/>}
                  {tool === "diagnosis" && <DiagnosisTool plants={plants} onOpen={openPlant}/>}
                  {tool === "identify" && <IdentificationTool settings={settings} onPrepare={preparePlant}/>}
                  {tool === "catalog" && <SpeciesCatalog settings={settings} onPrepare={preparePlant}/>}
                  {tool === "species" && <SpeciesLibrary settings={settings} onPrepare={preparePlant}/>}
                  {tool === "backup" && (
                    <BackupTool plants={plants} run={run} />
                  )}
                  {tool === "settings" && settings && (
                    <SettingsTool settings={settings} />
                  )}
                  {tool === "sensors" && (
                    <SensorsTool
                      plants={plants}
                      settings={settings}
                      run={run}
                    />
                  )}
                  {tool === "ai" && (
                    <section className="panel">
                      <div className="section-heading">
                        <h2>
                          <Sparkles size={19} />
                          Piano AI
                        </h2>
                        <button
                          className="button primary"
                          disabled={busy || !settings?.aiConfigured}
                          onClick={() =>
                            safeRun(
                              () => api("ai/analyze", { method: "POST" }),
                              "Analisi completata",
                            )
                          }
                        >
                          {busy ? (
                            <LoaderCircle className="spin" size={17} />
                          ) : (
                            <Sparkles size={17} />
                          )}
                          Analizza ora
                        </button>
                      </div>
                      <p className="muted">
                        {settings?.aiConfigured
                          ? `${settings.aiProvider} · ${settings.aiModel}. Analisi programmata alle ${settings.aiUpdateTime}. ${settings.autoApplyAI ? "Applicazione automatica attiva." : "Le modifiche richiedono la tua conferma."}`
                          : "Configura provider, modello e chiave nelle opzioni dell’add-on Home Assistant."}
                      </p>
                      <AIModelCatalog settings={settings} onChanged={()=>run(async()=>{},"Modello aggiornato")}/>
                      {settings?.aiStatus && <><p>{settings.aiStatus.summary}</p>{settings.aiStatus.notificationError && <p className="muted small-text">{settings.aiStatus.notificationError}</p>}</>}
                      <p className="muted small-text">L’analisi invia i dati testuali delle piante in modalità AI al provider configurato e può consumare credito API. Le foto non vengono inviate.</p>
                      {proposals.length ? (
                        proposals.map((p) => (
                          <div className="proposal" key={p.id}>
                            <h3>{p.plantName}</h3>
                            <div className="proposal-numbers">
                              <span>
                                Acqua{" "}
                                <b>
                                  {p.currentWateringDays} →{" "}
                                  {p.proposedWateringDays} g
                                </b>
                              </span>
                              <span>
                                Concime{" "}
                                <b>
                                  {p.currentFertilizingDays || "—"} →{" "}
                                  {p.proposedFertilizingDays} g
                                </b>
                              </span>
                            </div>
                            <p>{p.reason}</p><p className="muted small-text">{p.provider} · {p.model}</p>
                            {p.stale && (
                              <p className="danger">
                                La scheda è cambiata. Esegui una nuova analisi.
                              </p>
                            )}
                            <div className="button-row">
                              <button
                                className="button primary"
                                disabled={busy || p.stale}
                                onClick={() =>
                                  safeRun(
                                    () =>
                                      api(`proposals/${p.plantID}/apply`, {
                                        method: "POST",
                                      }),
                                    "Piano applicato",
                                  )
                                }
                              >
                                <Check size={16} />
                                Applica
                              </button>
                              <button
                                className="button secondary"
                                disabled={busy}
                                onClick={() =>
                                  safeRun(
                                    () =>
                                      api(`proposals/${p.plantID}`, {
                                        method: "DELETE",
                                      }),
                                    "Proposta rimossa",
                                  )
                                }
                              >
                                Rifiuta
                              </button>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="gentle-empty">
                          <Sparkles size={25} />
                          <p>Non ci sono proposte da esaminare.</p>
                        </div>
                      )}
                    </section>
                  )}
                </>
              )}
              <footer className="page-footer">
                <Leaf size={13} />
                {t("app.footer")}
              </footer>
            </>
          )}
        </div>
      </main>
      {selectedSummary && !selectedPlant && <aside className="detail">{detailError?<><p role="alert">{detailError}</p><button className="button primary" onClick={()=>setDetailRetry(v=>v+1)}>{t("common.retry")}</button></>:<p role="status">{t("app.detailOpening")}</p>}<button className="button secondary" onClick={()=>openPlant(null)}>{t("app.closeDetail")}</button></aside>}
      {!selectedSummary && ["today", "plants", "care"].includes(page) && (
        <aside className="detail empty-native-detail">
          <Leaf size={64} />
          <h2>{t("app.emptyDetailTitle")}</h2>
          <p>{t("app.emptyDetailText")}</p>
        </aside>
      )}
      {selectedPlant && (
        <PlantDetail
          plant={selectedPlant}
          products={products}
          settings={settings}
          onClose={() => openPlant(null)}
          onEdit={() => setPlantEditor(selectedPlant)}
          onAction={(kind, scheduled) =>
            setAction({ plant: selectedPlant, kind, scheduled })
          }
          onEditEvent={(event) =>
            setAction({ plant: selectedPlant, kind: event.kind, event })
          }
          onDelete={() =>
            setConfirm({
              title: `Eliminare ${selectedPlant.name}? Le sue cure verranno rimosse dall’archivio.`,
              run: async () => {
                await run(
                  () =>
                    api(
                      `plants/${selectedPlant.id}?version=${selectedPlant._version}`,
                      { method: "DELETE" },
                    ),
                  "Pianta eliminata",
                );
                openPlant(null);
              },
            })
          }
          onDeleteEvent={(id) =>
            setConfirm({
              title:
                "Eliminare questa registrazione? Le scadenze saranno ricalcolate.",
              run: async () => {
                await run(
                  () =>
                    api(
                      `plants/${selectedPlant.id}/events/${id}?version=${selectedPlant._version}`,
                      { method: "DELETE" },
                    ),
                  "Cura eliminata",
                );
              },
            })
          }
          run={run}
          busy={busy}
        />
      )}
      <nav className="bottom-tabs" aria-label={t("nav.main")}>
        {navigation.map((n) => (
          <button
            key={n.id}
            className={page === n.id ? "active" : ""}
            onClick={() => navigate(n.id)}
          >
            <span>
              <IOSIcon name={iosNavigation[n.id]} size={24} />
              {n.id === "care" && due.length > 0 && <b>{due.length}</b>}
            </span>
            {t(n.labelKey)}
          </button>
        ))}
      </nav>
      {plantEditor && (
        <PlantEditor
          plant={plantEditor === "new" ? undefined : plantEditor}
          seed={plantEditor === "new" ? plantSeed : undefined}
          settings={settings}
          products={products}
          rooms={rooms}
          busy={busy}
          onClose={() => {setPlantEditor(null);setPlantSeed(undefined)}}
          onSave={async (p) => {
            await run(async () => {
              const saved = await api<Plant>(
                plantEditor === "new"
                  ? "plants"
                  : `plants/${p.id}?version=${p._version}`,
                {
                  method: plantEditor === "new" ? "POST" : "PUT",
                  body: JSON.stringify(p),
                },
              );
              openPlant(saved.id);
            }, "Pianta salvata");
            setPlantEditor(null);setPlantSeed(undefined);
          }}
        />
      )}
      {productEditor && (
        <ProductEditor
          product={productEditor === "new" ? undefined : productEditor}
          busy={busy}
          onClose={() => setProductEditor(null)}
          onSave={async (p) => {
            await run(
              () =>
                api(
                  productEditor === "new"
                    ? "fertilizers"
                    : `fertilizers/${p.id}?version=${p._version}`,
                  {
                    method: productEditor === "new" ? "POST" : "PUT",
                    body: JSON.stringify(p),
                  },
                ),
              "Prodotto salvato",
            );
            setProductEditor(null);
          }}
        />
      )}
      {roundOpen && (
        <CareRound
          plants={plants}
          room={room}
          zone={settings?.timezone || "Europe/Rome"}
          onClose={() => setRoundOpen(false)}
          reload={reload}
        />
      )}
      {cycleProduct && (
        <TreatmentEditor
          plants={plants}
          products={products}
          initialProduct={cycleProduct}
          busy={busy}
          onClose={() => setCycleProduct(null)}
          onSave={async (plant, draft) => {
            await run(
              () =>
                api(`plants/${plant.id}/treatments?version=${plant._version}`, {
                  method: "POST",
                  body: JSON.stringify(draft),
                }),
              "Ciclo pianificato",
            );
            setCycleProduct(null);
          }}
        />
      )}
      {action && (
        <EventEditor
          action={action}
          busy={busy}
          onClose={() => setAction(null)}
          onSave={async (data) => {
            await run(
              () =>
                api(
                  `plants/${action.plant.id}/events${action.event ? `/${action.event.id}?version=${action.plant._version}` : ""}`,
                  {
                    method: action.event ? "PUT" : "POST",
                    body: JSON.stringify(data),
                  },
                ),
              "Cura registrata",
            );
            setAction(null);
          }}
        />
      )}
      {confirm && (
        <Modal title="Conferma eliminazione" onClose={() => setConfirm(null)}>
          <p>{confirm.title}</p>
          <div className="modal-actions">
            <button
              className="button secondary"
              onClick={() => setConfirm(null)}
            >
              Annulla
            </button>
            <button
              className="button destructive"
              disabled={busy}
              onClick={() => {
                void confirm
                  .run()
                  .then(() => setConfirm(null))
                  .catch(() => setConfirm(null));
              }}
            >
              Elimina
            </button>
          </div>
        </Modal>
      )}
      {notice && (
        <div className="toast" role="status">
          <CheckCircle2 size={19} />
          {notice}
        </div>
      )}
    </div>
  );
}
function PlantCard({ plant, onClick }: { plant: Plant; onClick: () => void }) {
  const { t } = useI18n();
  const { actionLabel, dueLabel } = useCareLabels();
  const next = plant._actions[0];
  return (
    <button className="plant-card" onClick={onClick}>
      <div className="card-image">
        <Avatar plant={plant} large />
        <span className="room-tag">
          <MapPin size={11} />
          {plant.room}
        </span>
      </div>
      <div className="plant-card-body">
        <small>{plant.species || plant.category}</small>
        <span className="ios-card-room">{plant.room}</span>
        <h3>{plant.name}</h3>
        <div className="card-next">
          {next ? (
            <>
              <Droplets size={14} />
              <span>{actionLabel(next)}</span>
              <b className={next.daysUntil < 0 ? "danger" : ""}>
                {dueLabel(next.daysUntil)}
              </b>
            </>
          ) : (
            <span>{t("care.noneScheduled")}</span>
          )}
        </div>
      </div>
    </button>
  );
}
function EmptyCollection({
  onAdd,
  onImport,
}: {
  onAdd: () => void;
  onImport: () => void;
}) {
  return (
    <section className="empty-collection">
      <div className="empty-leaf">
        <Sprout size={34} />
      </div>
      <h2>Facciamo spazio al verde.</h2>
      <p>
        Ogni pianta ha il suo ritmo.
        <br />
        Porta qui la tua collezione e iniziamo a conoscerlo.
      </p>
      <div className="button-row">
        <button className="button primary" onClick={onAdd}>
          <Plus size={17} />
          La prima pianta
        </button>
        <button className="button secondary" onClick={onImport}>
          Importa archivio
        </button>
      </div>
    </section>
  );
}
function PlantEditor({
  plant,
  seed,
  settings,
  products,
  rooms,
  busy,
  onClose,
  onSave,
}: {
  plant?: Plant;
  seed?: PlantSeed;
  settings?: Settings;
  products: Product[];
  rooms: string[];
  busy: boolean;
  onClose: () => void;
  onSave: (p: Plant) => Promise<void>;
}) {
  const { t } = useI18n();
  const [draft, setDraft] = useState<Plant>(() =>
    plant
      ? { ...plant }
      : {
          id: uid(),
          name: "",
          species: "",
          room: "Casa",
          category: "Tropicale",
          light: "Luce indiretta",
          wateringInterval: 7,
          fertilizingInterval: null,
          acquiredOn: todayISO(),
          lastWatered: todayISO(),
          notes: "",
          history: [],
          carePlanMode: "Manuale",
          _version: 0,
          _schedule: [],
          _actions: [],
          _treatments: [],
          ...seed?.draft,
        },
  );
  const [error, setError] = useState(""),
    [uploading, setUploading] = useState(false);
  const [seedPhoto,setSeedPhoto]=useState("");
  useEffect(()=>{if(!seed?.file)return;const url=URL.createObjectURL(seed.file);setSeedPhoto(url);return()=>URL.revokeObjectURL(url)},[seed?.file]);
  const set = (key: string, value: unknown) =>
    setDraft((d) => ({ ...d, [key]: value }));
  const upload = async (file?: File) => {
    if (!file) return;
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const p = await api<{ path: string }>("photos", {
        method: "POST",
        body: form,
      });
      set("photoPath", p.path);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setUploading(false);
    }
  };
  const inputDate = (value: string) =>
    new Date(value).toLocaleDateString("en-CA");
  return (
    <Modal
      title={plant ? "Modifica pianta" : "Una nuova pianta"}
      onClose={onClose}
    >
      <form
        onSubmit={async(e) => {
          e.preventDefault();setError("");setUploading(true);
          try{let value=draft;if(seed?.file&&!draft.photoPath){const form=new FormData();form.append("file",seed.file);const photo=await api<{path:string}>("photos",{method:"POST",body:form});value={...draft,photoPath:photo.path};setDraft(value)}await onSave(value)}catch(e){setError((e as Error).message)}finally{setUploading(false)}
        }}
      >
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <label className="photo-upload">
          {(photoURL(draft.photoPath) || seedPhoto) ? (
            <img
              src={photoURL(draft.photoPath, true) || seedPhoto}
              alt="Foto della pianta"
            />
          ) : (
            <Camera size={28} />
          )}
          <span>
            {uploading ? "Caricamento…" : "Scegli una fotografia"}
            <small>JPEG, PNG o WebP · max 20 MB</small>
          </span>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            disabled={uploading}
            onChange={(e) => void upload(e.target.files?.[0])}
          />
        </label>
        {seed && <p className="muted small-text">Controlla nome, specie, ambiente e frequenze prima di salvare. Il riconoscimento non conferma automaticamente il piano di cura.</p>}
        <div className="form-grid">
          <label>
            Nome della pianta
            <input
              autoFocus
              required
              maxLength={200}
              value={draft.name}
              placeholder="Come la chiami?"
              onChange={(e) => set("name", e.target.value)}
            />
          </label>
          <label>
            Specie
            <input
              value={draft.species}
              placeholder="Es. Monstera deliciosa"
              onChange={(e) => set("species", e.target.value)}
            />
          </label>
          <label>
            Ambiente
            <input
              required
              list="rooms"
              value={draft.room}
              onChange={(e) => set("room", e.target.value)}
            />
            <datalist id="rooms">
              {rooms.map((r) => (
                <option key={r} value={r} />
              ))}
            </datalist>
          </label>
          <label>
            Categoria
            <select
              value={draft.category}
              onChange={(e) => set("category", e.target.value)}
            >
              {categories.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
          <label>
            Esposizione
            <select
              value={draft.light}
              onChange={(e) => set("light", e.target.value)}
            >
              {[
                "Luce bassa",
                "Luce indiretta",
                "Luce intensa",
                "Sole diretto",
              ].map((l) => (
                <option key={l}>{l}</option>
              ))}
            </select>
          </label>
          <label>Famiglia botanica<input value={draft.family || ""} maxLength={300} onChange={e=>set("family",e.target.value)} placeholder="Es. Araceae"/></label>
          <label>
            Piano di cura
            <select
              value={draft.carePlanMode || "Manuale"}
              onChange={(e) => set("carePlanMode", e.target.value)}
            >
              <option>Manuale</option>
              <option>AI</option>
              {draft.carePlanMode === "Intelligente" && (
                <option>Intelligente</option>
              )}
            </select>
          </label>
          <label>
            Annaffiatura · giorni
            <input
              type="number"
              min={1}
              max={120}
              required
              value={draft.wateringInterval}
              onChange={(e) => set("wateringInterval", Number(e.target.value))}
            />
          </label>
          <label>
            Concimazione · giorni
            <input
              type="number"
              min={1}
              max={365}
              placeholder="Non programmata"
              value={draft.fertilizingInterval ?? ""}
              onChange={(e) =>
                set(
                  "fertilizingInterval",
                  e.target.value ? Number(e.target.value) : null,
                )
              }
            />
          </label>
          <label>
            Acquisita il
            <input
              type="date"
              required
              value={inputDate(draft.acquiredOn)}
              onChange={(e) => {
                if (e.target.value)
                  set(
                    "acquiredOn",
                    new Date(e.target.value + "T12:00:00").toISOString(),
                  );
              }}
            />
          </label>
          <label>
            Ultima annaffiatura
            <input
              type="date"
              required
              value={inputDate(draft.lastWatered)}
              onChange={(e) => {
                if (e.target.value)
                  set(
                    "lastWatered",
                    new Date(e.target.value + "T12:00:00").toISOString(),
                  );
              }}
            />
          </label>
          <label className="full">
            Fertilizzante associato
            <select
              value={draft.fertilizerProductID || ""}
              onChange={(e) =>
                set("fertilizerProductID", e.target.value || null)
              }
            >
              <option value="">Nessuno</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </label>
        </div>
        <details className="form-details">
          <summary>Altre attività e vaso</summary>
          <div className="form-grid">
            {[
              ["rotationInterval", "Rotazione"],
              ["inspectionInterval", "Controllo salute"],
              ["repottingInterval", "Rinvaso"],
              ["pruningInterval", "Potatura"],
              ["progressInterval", "Diario di crescita"],
            ].map(([key, label]) => (
              <label key={key}>
                {label} · giorni
                <input
                  type="number"
                  min={1}
                  max={3650}
                  placeholder="Non programmata"
                  value={
                    (draft as unknown as Record<string, number>)[key] ?? ""
                  }
                  onChange={(e) =>
                    set(key, e.target.value ? Number(e.target.value) : null)
                  }
                />
              </label>
            ))}
            <label>
              Diametro vaso · cm
              <input
                type="number"
                min={1}
                max={500}
                value={draft.potDiameterCM ?? ""}
                onChange={(e) =>
                  set(
                    "potDiameterCM",
                    e.target.value ? Number(e.target.value) : null,
                  )
                }
              />
            </label>
            <label>
              Materiale
              <select
                value={draft.potMaterial || ""}
                onChange={(e) => set("potMaterial", e.target.value || null)}
              >
                <option value="">Non indicato</option>
                {[
                  "Plastica",
                  "Terracotta",
                  "Ceramica",
                  "Ceramica smaltata",
                  "Ceramica non smaltata",
                  "Tessuto",
                  "Auto-irrigante",
                  "Altro",
                ].map((m) => (
                  <option key={m}>{m}</option>
                ))}
              </select>
            </label>
          </div>
          <label className="check-label">
            <input
              type="checkbox"
              checked={draft.potHasDrainage === true}
              onChange={(e) => set("potHasDrainage", e.target.checked)}
            />
            Vaso con fori di drenaggio
          </label>
        </details>
        <label>
          {t("event.note")}
          <textarea
            rows={3}
            value={draft.notes}
            onChange={(e) => set("notes", e.target.value)}
            placeholder="Le sue abitudini, il tuo promemoria…"
          />
        </label>
        {draft.carePlanMode === "Intelligente" && (
          <p className="muted">
            Per ricalcolare gli intervalli usa Configura piano intelligente nella scheda. Puoi tornare a Manuale conservando gli intervalli attuali.
          </p>
        )}
        <div className="modal-actions">
          <button type="button" className="button secondary" onClick={onClose}>
            {t("common.cancel")}
          </button>
          <button className="button primary" disabled={busy || uploading}>
            {busy ? (
              <LoaderCircle className="spin" size={16} />
            ) : (
              <Check size={16} />
            )}
            Salva pianta
          </button>
        </div>
        {draft.species && <details><summary>Consulta la scheda botanica della specie</summary><BotanicalLookup scientificName={draft.species} configured={!!(settings?.services?.perenual||settings?.services?.openplantbook)}/></details>}
      </form>
    </Modal>
  );
}
function ProductEditor({
  product,
  busy,
  onClose,
  onSave,
}: {
  product?: Product;
  busy: boolean;
  onClose: () => void;
  onSave: (p: Product) => Promise<void>;
}) {
  const { t } = useI18n();
  const [p, set] = useState<Product>(
    product || {
      id: uid(),
      name: "",
      brand: "",
      notes: "",
      form: "Liquido",
      category: "Fertilizzante",
      dosage: "",
      applicationMethod: "",
      _version: 0,
    },
  );
  const [error, setError] = useState(""),[uploading,setUploading]=useState(false);
  const upload=async(file?:File)=>{if(!file)return;setUploading(true);setError("");try{const form=new FormData();form.append("file",file);const photo=await api<{path:string}>("photos",{method:"POST",body:form});set(p=>({...p,photoPath:photo.path}))}catch(e){setError((e as Error).message)}finally{setUploading(false)}};
  return (
    <Modal
      title={product ? "Modifica prodotto" : "Nuovo prodotto"}
      onClose={onClose}
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void onSave(p).catch((e) => setError(e.message));
        }}
      >
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <label className="photo-upload product-photo-upload">
          {photoURL(p.photoPath)?<img src={photoURL(p.photoPath,true)} alt="Foto del prodotto"/>:<Camera size={28}/>}
          <span>{uploading?"Caricamento…":"Scegli una fotografia del prodotto"}<small>JPEG, PNG o WebP</small></span>
          <input type="file" accept="image/jpeg,image/png,image/webp" disabled={busy||uploading} onChange={e=>void upload(e.target.files?.[0])}/>
        </label>
        <label>
          Nome
          <input
            autoFocus
            required
            value={p.name}
            onChange={(e) => set({ ...p, name: e.target.value })}
          />
        </label>
        <label>
          Marca
          <input
            value={p.brand}
            onChange={(e) => set({ ...p, brand: e.target.value })}
          />
        </label>
        <div className="form-grid">
          <label>
            Categoria
            <select
              value={p.category || "Fertilizzante"}
              onChange={(e) => set({ ...p, category: e.target.value })}
            >
              {[
                "Fertilizzante",
                "Radicante",
                "Antiparassitario",
                "Fungicida",
                "Biostimolante",
                "Ammendante",
                "Altro trattamento",
              ].map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
          <label>
            Formato
            <select
              value={p.form || "Liquido"}
              onChange={(e) => set({ ...p, form: e.target.value })}
            >
              {[
                "Liquido",
                "Granulare",
                "Bastoncini",
                "Polvere",
                "Organico",
                "Altro",
              ].map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
        </div>
        <label>
          Dose del produttore
          <input
            value={p.dosage || ""}
            onChange={(e) => set({ ...p, dosage: e.target.value })}
            placeholder="Es. quantità per litro"
          />
        </label>
        <label>
          Modalità d’uso
          <input
            value={p.applicationMethod || ""}
            onChange={(e) => set({ ...p, applicationMethod: e.target.value })}
            placeholder="Es. diluire nell’acqua o applicazione fogliare"
          />
        </label>
        <label>
          Intervallo del produttore · giorni
          <input
            type="number"
            min={1}
            max={365}
            value={p.applicationIntervalDays ?? ""}
            onChange={(e) =>
              set({
                ...p,
                applicationIntervalDays: e.target.value
                  ? Number(e.target.value)
                  : null,
              })
            }
          />
        </label>
        <label>
          Indicazioni e dosaggio
          <textarea
            rows={4}
            value={p.notes}
            onChange={(e) => set({ ...p, notes: e.target.value })}
          />
        </label>
        <div className="modal-actions">
          <button type="button" className="button secondary" onClick={onClose}>
            {t("common.cancel")}
          </button>
          <button disabled={busy || uploading} className="button primary">
            Salva prodotto
          </button>
        </div>
      </form>
    </Modal>
  );
}
function EventEditor({
  action,
  busy,
  onClose,
  onSave,
}: {
  action: CareSelection;
  busy: boolean;
  onClose: () => void;
  onSave: (data: unknown) => Promise<void>;
}) {
  const { t } = useI18n();
  const { kindLabel } = useCareLabels();
  const localDate = (s: string) => {
    const d = new Date(s);
    return new Date(d.getTime() - d.getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 16);
  };
  const [health, setHealth] = useState(action.event?.health || "Buona");
  const [symptoms,setSymptoms]=useState<string[]>([]),[areas,setAreas]=useState<string[]>([]),[problem,setProblem]=useState(''),[nextAction,setNextAction]=useState('');
  const requiresHealth=['Controlla salute','Aggiorna progressi'].includes(action.kind);
  const isNewInspection=action.kind==='Controlla salute'&&!action.event;
  const toggleHealthOption=(value:string,values:string[],setValues:(items:string[])=>void)=>setValues(values.includes(value)?values.filter(v=>v!==value):[...values,value]);
  const [id] = useState(action.event?.id || uid()),
    [date, setDate] = useState(localDate(action.event?.date || todayISO())),
    [note, setNote] = useState(action.event?.note || ""),
    [postponed, setPostponed] = useState(action.event?.status === "postponed"),
    [until, setUntil] = useState(
      localDate(
        action.event?.postponedUntil ||
          new Date(Date.now() + 86400000).toISOString(),
      ),
    ),
    [feeding, setFeeding] = useState(false),
    [error, setError] = useState("");
  return (
    <Modal title={action.event ? t("event.editTitle") : t("event.confirmTitle")} onClose={onClose}>
      <div className="care-confirm-heading"><span className="care-confirm-symbol">{(() => {const Icon=eventIcon(action.kind);return <Icon size={26}/>})()}</span><p>{kindLabel(action.kind)} · {action.plant.name}</p></div>
      <ActionGuide kind={action.kind} expanded/>
      <form className="care-event-form"
        onSubmit={(e) => {
          e.preventDefault();
          void onSave({
            id,
            kind: action.kind,
            date: new Date(date).toISOString(),
            note: isNewInspection ? healthCheckNote(note,symptoms,areas,problem,nextAction) : note,
            status: postponed ? "postponed" : "completed",
            postponedUntil: postponed ? new Date(until).toISOString() : null,
            health:
              requiresHealth
                ? health
                : action.event?.health,
            includingFertilizing: feeding,
            treatmentPlanID:
              action.event?.treatmentPlanID ||
              action.scheduled?.treatmentPlanID ||
              null,
            productID:
              action.event?.productID || action.scheduled?.productID || null,
            expectedApplicationNumber: action.scheduled?.applicationNumber,
            scheduledDueDate: !action.event
              ? action.scheduled?.dueDate
              : undefined,
          }).catch((e) => setError(e.message));
        }}
      >
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        {action.scheduled?.reason && (
          <p className="info-note">{action.scheduled.reason}</p>
        )}
        <label>
          {t("event.when")}
          <input
            type="datetime-local"
            required
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </label>
        <label className="check-label">
          <input
            type="checkbox"
            checked={postponed}
            onChange={(e) => setPostponed(e.target.checked)}
          />
          {t("event.postpone")}
        </label>
        {postponed && (
          <label>
            {t("event.postponeUntil")}
            <input
              type="datetime-local"
              required
              value={until}
              onChange={(e) => setUntil(e.target.value)}
            />
          </label>
        )}
        {action.kind === "Annaffia" &&
          !postponed &&
          !action.event &&
          (action.scheduled?.canIncludeFertilizing ||
            action.scheduled?.includesFertilizing ||
            (!action.scheduled &&
              action.plant._actions.find((a) => a.kind === "Annaffia")
                ?.canIncludeFertilizing)) && (
            <>
              <label className="check-label">
                <input
                  type="checkbox"
                  checked={feeding}
                  onChange={(e) => setFeeding(e.target.checked)}
                />
                {t("event.feedTogether")}
              </label>
              <p className="muted small-text">
                {t("event.feedHint")}
              </p>
            </>
          )}
        {requiresHealth&&<fieldset className="care-health-options"><legend>{t("event.healthState")}</legend><div>{healthStates.map(h=><button type="button" key={h} aria-pressed={health===h} onClick={()=>setHealth(h)}><IOSIcon name={h==='Eccellente'?'sparkles':'health'} size={22}/>{t(healthStateKeys[h])}</button>)}</div></fieldset>}
        {isNewInspection&&<section className="care-health-details"><fieldset className="care-health-options"><legend>{t("event.observed")}</legend><div>{healthSymptoms.map(value=><button type="button" key={value} aria-pressed={symptoms.includes(value)} onClick={()=>toggleHealthOption(value,symptoms,setSymptoms)}>{symptoms.includes(value)&&<Check size={16}/>} {t(symptomKeys[value] ?? "event.observed")}</button>)}</div></fieldset><fieldset className="care-health-options"><legend>{t("event.areas")}</legend><div>{healthAreas.map(value=><button type="button" key={value} aria-pressed={areas.includes(value)} onClick={()=>toggleHealthOption(value,areas,setAreas)}>{areas.includes(value)&&<Check size={16}/>} {t(areaKeys[value] ?? "event.areas")}</button>)}</div></fieldset><label>{t("event.problem")}<textarea rows={2} value={problem} onChange={e=>setProblem(e.target.value)}/></label><label>{t("event.nextAction")}<textarea rows={2} value={nextAction} onChange={e=>setNextAction(e.target.value)}/></label></section>}
        <label>
          {t("event.note")}
          <textarea
            rows={3}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder={t("event.notePlaceholder")}
          />
        </label>
        <div className="modal-actions">
          <button className="button secondary" type="button" onClick={onClose}>
            {t("common.cancel")}
          </button>
          <button className="button primary" disabled={busy}>
            <Check size={16} />
            {postponed ? t("event.savePostpone") : action.event ? t("event.saveChanges") : t("event.complete")}
          </button>
        </div>
      </form>
    </Modal>
  );
}
function PlantDetail({
  plant,
  products,
  settings,
  onClose,
  onEdit,
  onAction,
  onEditEvent,
  onDelete,
  onDeleteEvent,
  run,
  busy,
}: {
  plant: Plant;
  products: Product[];
  settings?: Settings;
  onClose: () => void;
  onEdit: () => void;
  onAction: (kind: string, scheduled?: Action) => void;
  onEditEvent: (event: Plant["history"][number]) => void;
  onDelete: () => void;
  onDeleteEvent: (id: string) => void;
  run: (fn: () => Promise<unknown>, message?: string) => Promise<void>;
  busy: boolean;
}) {
  const { t, plural, locale } = useI18n();
  const { actionLabel, dueLabel, kindLabel, dateLabel } = useCareLabels();
  const [tab, setTab] = useState("Scheda"),
    [error, setError] = useState(""),
    [measurements, setMeasurements] = useState<Measure[]>([]),
    [healthOpen,setHealthOpen]=useState(false),
    [labelOpen,setLabelOpen]=useState(false),
    [growthOpen, setGrowthOpen] = useState(false),
    [adaptiveOpen, setAdaptiveOpen] = useState(false),
    [phoneSection,setPhoneSection]=useState(""),
    [measureRevision, setMeasureRevision] = useState(0);
  useEffect(() => {
    setTab("Scheda");
    setPhoneSection("");
    setError("");
  }, [plant.id]);
  useEffect(() => {
    if (tab !== "Misure") return;
    let active=true;
    setMeasurements([]);setError('');
    api<Measure[]>(`plants/${plant.id}/measurements`)
      .then(values=>{if(active)setMeasurements(values)})
      .catch(e=>{if(active)setError(e.message)});
    return ()=>{active=false};
  }, [plant.id, tab]);
  const history = plant.history
    .filter((e) => !e.deletedAt)
    .sort((a, b) => b.date.localeCompare(a.date));
  const detailScrollRef=useRef<HTMLDivElement>(null);
  useEffect(()=>{detailScrollRef.current?.scrollTo({top:0})},[plant.id]);
  const [carePage,setCarePage]=useState(1),[growthPage,setGrowthPage]=useState(1);
  useEffect(()=>{setCarePage(1);setGrowthPage(1)},[plant.id,plant._version]);
  const growth=(plant.growthEntries||[]).slice().sort((a,b)=>b.date.localeCompare(a.date));
  const product = products.find((p) => p.id === plant.fertilizerProductID);
  const phone=useIOSLayout();
  useEffect(()=>{
    if(!phone||!phoneSection)return;
    const header=detailScrollRef.current?.querySelector<HTMLElement>(`.ios-section-card[data-section="${phoneSection}"]>button`);
    header?.scrollIntoView({block:'start',behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
  },[phone,phoneSection]);
  const detailBody=(
        <div className="detail-body">
          <div className="eyebrow">
            {plant.category} · {plant.room}
          </div>
          <h2 className="plant-title">{plant.name}</h2>
          <p className="scientific">
            {plant.species || t("detail.speciesUnknown")}
          </p>
          {!plant.photoPath &&
            plant.catalogImageURL &&
            plant.catalogImageAttribution && (
              <p className="muted small-text">
                {t("detail.photoCredit", { credit: plant.catalogImageAttribution })}
              </p>
            )}
          <div className="quick-actions">
            <button
              className="button primary"
              onClick={() => onAction("Annaffia")}
            >
              <Droplets size={17} />
              {t("detail.water")}
            </button>
            <select
              aria-label={t("detail.otherCareAria")}
              value=""
              onChange={(e) => {
                if (e.target.value) onAction(e.target.value);
              }}
            >
              <option value="">{t("detail.otherCare")}</option>
              {kinds
                .filter((k) => k !== "Annaffia")
                .map((k) => (
                  <option key={k} value={k}>{kindLabel(k)}</option>
                ))}
            </select>
          </div>
          <div className="detail-tabs">
            {detailTabs.map((tabItem) => (
              <button
                key={tabItem.id}
                className={tab === tabItem.id ? "active" : ""}
                onClick={() => setTab(tabItem.id)}
              >
                {t(tabItem.key)}
              </button>
            ))}
          </div>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          {tab === "Scheda" && (
            <>
              <button className="button secondary" onClick={()=>setLabelOpen(true)}>{t("detail.qr")}</button>
              <div className="detail-section ios-plan-content">
                <h3>{t("detail.rhythm")}</h3>
                {plant._actions.map((a) => {
                  const Icon = eventIcon(a.kind);
                  return (
                    <button
                      className="schedule-line"
                      key={a.id}
                      onClick={() => onAction(a.kind, a)}
                    >
                      <span className="schedule-icon">
                        <Icon size={17} />
                      </span>
                      <span>
                        <strong>{actionLabel(a)}</strong>
                        <small>
                          {a.reason || plural("care.everyDays", a.intervalDays)}
                        </small>
                      </span>
                      <span className={a.daysUntil < 0 ? "danger" : ""}>
                        {dueLabel(a.daysUntil)}
                      </span>
                      <ChevronRight size={15} />
                    </button>
                  );
                })}
              </div>
              <div className="detail-section">
                <h3>{t("detail.home")}</h3>
                <div className="fact">
                  <Sun size={18} />
                  <span>{t("detail.exposure")}</span>
                  <strong>{plant.light}</strong>
                </div>
                <div className="fact">
                  <MapPin size={18} />
                  <span>{t("detail.room")}</span>
                  <strong>{plant.room}</strong>
                </div>
                <div className="fact">
                  <Settings2 size={18} />
                  <span>{t("detail.plan")}</span>
                  <strong>{t(planModeKeys[plant.carePlanMode || "Manuale"] ?? "detail.planMode.manual")}</strong>
                </div>
                {plant.potDiameterCM && (
                  <div className="fact">
                    <Flower2 size={18} />
                    <span>{t("detail.pot")}</span>
                    <strong>
                      {plant.potDiameterCM} cm · {plant.potMaterial || "—"}
                    </strong>
                  </div>
                )}
                {product && (
                  <div className="fact">
                    <FlaskConical size={18} />
                    <span>{t("detail.product")}</span>
                    <strong>{product.name}</strong>
                  </div>
                )}
              </div>
              {plant._learning && (
                <div className="learning ios-plan-content">
                  <Sprout size={19} />
                  <h3>{t("detail.learning")}</h3>
                  <p>{plant._learning.explanation}</p>
                  <small>
                    {t("detail.confidence", { percent: Math.round(plant._learning.confidence * 100) })} ·
                    {plant.carePlanMode === "Intelligente" ? t("detail.learningPlan") : t("detail.informative")}
                  </small>
                </div>
              )}
              <div className="detail-section ios-plan-content">
                <button className="button secondary" onClick={()=>{if(phone&&plant.carePlanMode==='Manuale')onEdit();else if(phone&&plant.carePlanMode==='AI'){setPhoneSection('AI');setTab('AI')}else setAdaptiveOpen(true)}}><Sprout size={16}/>{phone&&plant.carePlanMode==='Manuale'?t('detail.planEditManual'):phone&&plant.carePlanMode==='AI'?t('detail.planSetAI'):plant.adaptivePlan ? t('detail.planRecalc') : t('detail.planConfigure')}</button>
              </div>
              {plant.adaptivePlan && (
                <div className="detail-section ios-plan-content">
                  <h3>{t("detail.smartPlan")}</h3>
                  <p>
                    {plant.adaptivePlan.seasonName} ·{" "}
                    {plant.adaptivePlan.placement}
                  </p>
                  <p className="muted small-text">{plant.adaptivePlan.locationName} · {plant.adaptivePlan.averageTemperature} °C · {plant.adaptivePlan.relativeHumidity}% umidità · {plant.adaptivePlan.precipitationNextWeek} mm in 7 giorni</p>
                  <p className="muted small-text">{plant.adaptivePlan.weatherEnabled ? t("detail.weatherOn") : t("detail.weatherOff")} · {t("detail.calculated", { date: dateLabel(plant.adaptivePlan.generatedAt) })}</p>
                  {plant.adaptivePlan.rationale?.map((r, i) => (
                    <p className="muted small-text" key={i}>
                      {r}
                    </p>
                  ))}
                </div>
              )}
              {plant.adaptivePlan?.climateRevisionHistory?.length ? <details className="detail-section ios-plan-content"><summary>{t("detail.climateHistory")}</summary>{[...plant.adaptivePlan.climateRevisionHistory].reverse().map(r=><p className="small-text" key={r.id}>{dateLabel(r.date)} · {t("detail.climateLine", { from: r.previousWateringDays, to: r.newWateringDays, feedFrom: r.previousFertilizingDays, feedTo: r.newFertilizingDays })}</p>)}</details> : null}
              {!phone&&<CareInsights plant={plant} revision={measureRevision}/>}
              <div className="detail-section safety-section">
                <h3>{t("detail.safety")}</h3>
                {plant.safetyProfile ? (
                  <>
                    <p>
                      {t("detail.pets")}{" "}
                      {plant.safetyProfile.poisonousToPets === true
                        ? t("detail.petsRisk")
                        : plant.safetyProfile.poisonousToPets === false
                          ? t("detail.petsSafe")
                          : t("detail.petsUnknown")}
                      .
                    </p>
                    <p>
                      Persone:{" "}
                      {plant.safetyProfile.poisonousToHumans === true
                        ? "rischio noto"
                        : plant.safetyProfile.poisonousToHumans === false
                          ? "non tossica secondo la fonte"
                          : "dato non disponibile"}
                      .
                    </p>
                    <small className="muted">
                      Fonte: {plant.safetyProfile.sourceName}
                    </small>
                  </>
                ) : (
                  <p className="muted">
                    Profilo non disponibile. L’assenza di una scheda non
                    significa che la pianta sia sicura.
                  </p>
                )}
              </div>
              <div className="detail-section">
                <h3>Le tue note</h3>
                <p className="preserve">
                  {plant.notes || "Nessuna nota, per ora."}
                </p>
              </div>
              <button className="text-button danger" onClick={onDelete}>
                <Trash2 size={15} />
                Elimina pianta
              </button>
            </>
          )}
          {tab === "Trattamenti" && (
            <TreatmentPanel
              plant={plant}
              products={products}
              run={run}
              busy={busy}
              onAction={(a) => onAction(a.kind, a)}
            />
          )}
          {tab === "Diario" && (
            <>
              <div className="ios-growth-content">
              <div className="section-heading">
                <h3>Storie di crescita</h3>
                <button
                  className="icon-button"
                  aria-label="Nuovo aggiornamento"
                  onClick={() => setGrowthOpen(true)}
                >
                  <Plus size={19} />
                </button>
              </div>
              {growth.slice((growthPage-1)*12,growthPage*12).map((g) => (
                  <div className="growth-entry" key={g.id}>
                    <small>
                      {dateLabel(g.date)} · {t(healthStateKeys[g.health] ?? "health.state.good")}
                      {g.heightCM ? ` · ${g.heightCM} cm` : ""}
                    </small>
                    <p>{g.note}</p>
                    <div className="growth-photos">
                      {g.photoPaths.map(
                        (p) =>
                          photoURL(p) && (
                            <a
                              href={photoURL(p)}
                              target="_blank"
                              rel="noreferrer"
                              key={p}
                            >
                              <img
                                src={photoURL(p, true)}
                                alt={t("detail.growthPhotoAlt", { date: dateLabel(g.date) })}
                                loading="lazy"
                              />
                            </a>
                          ),
                      )}
                    </div>
                  </div>
                ))}
              <ArchivePagination label="Storie di crescita" page={growthPage} size={12} total={growth.length} onPage={setGrowthPage}/>
              </div><div className="ios-history-content">
              <h3 className="history-title">Cronologia delle cure</h3>
              {history.length ? (
                history.slice((carePage-1)*50,carePage*50).map((e) => {
                  const Icon = eventIcon(e.kind);
                  return (
                    <div className="history-event" key={e.id}>
                      <span className="timeline-icon">
                        <Icon size={16} />
                      </span>
                      <div>
                        <strong>
                          {e.kind}
                          {e.status === "postponed" ? " · Rinviata" : ""}
                        </strong>
                        <small>
                          {new Date(e.date).toLocaleString("it-IT", {
                            dateStyle: "medium",
                            timeStyle: "short",
                          })}
                        </small>
                        {e.note && <p>{e.note}</p>}
                        {e.postponedUntil && (
                          <small>
                            {t("detail.postponedTo", { date: dateLabel(e.postponedUntil) })}
                          </small>
                        )}
                        <div className="history-actions">
                          <button
                            className="text-button"
                            onClick={() => onEditEvent(e)}
                          >
                            Modifica
                          </button>
                          <button
                            className="text-button danger"
                            onClick={() => onDeleteEvent(e.id)}
                          >
                            Elimina
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="gentle-empty">
                  <BookOpen size={23} />
                  <p>Le cure registrate racconteranno la sua storia.</p>
                </div>
              )}
              </div>
            </>
          )}
          {tab === "Diario" && <div className="ios-history-content"><ArchivePagination label="Cure della pianta" page={carePage} size={50} total={history.length} onPage={setCarePage}/></div>}
          {tab === "Misure" && (
            <>
              <h3>Osservazioni e sensori</h3>
              <p className="muted">
                Le misure descrivono una condizione: una singola lettura non
                equivale a una diagnosi.
              </p>
              <ManualMeasurement
                plant={plant}
                onSave={async (data) => {
                  await run(
                    () =>
                      api(`plants/${plant.id}/measurements`, {
                        method: "POST",
                        body: JSON.stringify(data),
                      }),
                    "Misura salvata",
                  );
                  setMeasurements(await api(`plants/${plant.id}/measurements`));
                  setMeasureRevision(v=>v+1);
                }}
              />
              {measurements.map((m) => (
                <div className="measurement" key={m.id}>
                  <span>
                    <strong>
                      {(
                        {
                          illuminance: "Luce",
                          moisture: "Terreno",
                          humidity: "Umidità",
                          temperature: "Temperatura",
                          conductivity: "Conducibilità",
                        } as Record<string, string>
                      )[m.kind] || m.kind}
                    </strong>
                    <small>
                      {new Date(m.measured_at).toLocaleString("it-IT")}
                    </small>
                    <small>
                      {m.entity_id === "manual"
                        ? "Inserita a mano"
                        : m.entity_id}
                    </small>
                  </span>
                  <b>
                    {Number(m.value).toLocaleString("it-IT", {
                      maximumFractionDigits: 1,
                    })}{" "}
                    {m.unit}
                  </b>
                </div>
              ))}
              {!measurements.length && (
                <p className="muted">Nessuna misura registrata.</p>
              )}
            </>
          )}
          {tab === "Salute" && <HealthAlbum plant={plant} onNew={()=>setHealthOpen(true)}/>}
          {tab === "Guida" && <>{phone&&<BotanicalLookup scientificName={plant.species} configured={!!(settings?.services?.openplantbook||settings?.services?.perenual)}/>}<PlantKnowledge plant={plant}/></>}
          {tab === "AI" && <PlantAssistant key={plant.id} plant={plant} settings={settings} run={run}/>}

        </div>
  );
  return (
    <aside className={`detail ${phoneSection?"ios-section-open":""} ${phoneSection==="Sicurezza"?"ios-safety-open":""} ${phoneSection==="Piano"?"ios-plan-open":""} ${phoneSection==="Crescita"?"ios-growth-open":""} ${phoneSection==="Diario"?"ios-history-open":""}`}>
      <header className="detail-top">
        <button
          className="icon-button"
          aria-label="Chiudi scheda"
          onClick={onClose}
        >
          <ArrowLeft size={20} className="desktop-symbol"/><ChevronLeft size={24} className="mobile-symbol"/>
        </button>
        <span className="desktop-detail-caption">LA TUA PIANTA</span><span className="ios-detail-caption">{plant.name}</span>
        <button
          className="icon-button desktop-detail-edit"
          aria-label="Modifica pianta"
          onClick={onEdit}
        >
          <Pencil size={18} />
        </button>
        <button className="ios-plan-button" aria-label={plant.carePlanMode==='AI'?'Imposta piano AI':plant.carePlanMode==='Intelligente'?'Configura piano intelligente':'Modifica piano manuale'} onClick={()=>{if(plant.carePlanMode==='AI'){setPhoneSection('AI');setTab('AI')}else if(plant.carePlanMode==='Intelligente'){setAdaptiveOpen(true)}else onEdit()}}>{plant.carePlanMode==='AI'?<IOSIcon name="brain" size={25}/>:plant.carePlanMode==='Intelligente'?<Sprout size={25}/>:<Pencil size={23}/>}</button>
        <details className="ios-detail-more"><summary aria-label="Altre azioni della pianta"><Ellipsis size={23}/></summary><div><button className="button secondary" onClick={onEdit}><Pencil size={17}/>Modifica pianta</button><label>Registra una cura<select aria-label="Registra una cura" value="" onChange={e=>{if(e.target.value)onAction(e.target.value)}}><option value="">Scegli attività…</option>{kinds.map(k=><option key={k}>{k}</option>)}</select></label></div></details>
      </header>
      <div className="detail-scroll" ref={detailScrollRef}>
        {phone&&<IOSPlantOverview plant={plant} products={products} openSection={phoneSection} sectionContent={phoneSection==='Consigli'?<CareInsights plant={plant} revision={measureRevision}/>:detailBody} onAction={onAction} onLabel={()=>setLabelOpen(true)} onSection={section=>{setPhoneSection(section);setTab(!section||['Piano','Sicurezza','Consigli','Prodotto','Note'].includes(section)?'Scheda':section==='Crescita'?'Diario':section)}}/>}
        {!phone&&<Avatar plant={plant} large/>}
        {!phone && detailBody}
      </div>
      {healthOpen && <HealthPhotoEditor key={plant.id} plant={plant} onClose={()=>setHealthOpen(false)} onSaved={()=>run(async()=>{},"Controllo sanitario salvato")}/>}
      {labelOpen && <PlantLabel plant={plant} settings={settings} onClose={()=>setLabelOpen(false)}/>}
      {adaptiveOpen && <AdaptiveEditor key={plant.id} plant={plant} onClose={()=>setAdaptiveOpen(false)} onApplied={()=>run(async()=>{}, "Piano intelligente applicato")}/>}
      {growthOpen && (
        <GrowthEditor
          busy={busy}
          onClose={() => setGrowthOpen(false)}
          onSave={async (value) => {
            await run(
              () =>
                api(`plants/${plant.id}/growth`, {
                  method: "POST",
                  body: JSON.stringify(value),
                }),
              "Diario aggiornato",
            );
            setGrowthOpen(false);
          }}
        />
      )}
    </aside>
  );
}
function ManualMeasurement({
  plant,
  onSave,
}: {
  plant: Plant;
  onSave: (data: unknown) => Promise<void>;
}) {
  const { t } = useI18n();
  const [kind, setKind] = useState("illuminance"),
    [value, setValue] = useState(""),
    [error, setError] = useState("");
  return (
    <form
      className="manual-measure"
      onSubmit={(e) => {
        e.preventDefault();
        void onSave({
          kind,
          value: Number(value),
          unit: (
            {
              illuminance: "lx",
              moisture: "%",
              humidity: "%",
              temperature: "°C",
              conductivity: "µS/cm",
            } as Record<string, string>
          )[kind],
        })
          .then(() => setValue(""))
          .catch((e) => setError(e.message));
      }}
    >
      <label>
        {t("measure.type")}
        <select value={kind} onChange={(e) => setKind(e.target.value)}>
          <option value="illuminance">{t("measure.light")}</option>
          <option value="moisture">{t("measure.soilMoisture")}</option>
          <option value="humidity">{t("measure.airHumidity")}</option>
          <option value="temperature">{t("measure.temperature")}</option>
          <option value="conductivity">{t("measure.conductivity")}</option>
        </select>
      </label>
      <label>
        {t("measure.value")}
        <input
          aria-label={t("measure.valueAria", { name: plant.name })}
          type="number"
          required
          step="any"
          value={value}
          onChange={(e) => setValue(e.target.value)}
        />
      </label>
      <button className="button secondary">{t("measure.save")}</button>
      {error && <p className="form-error">{error}</p>}
    </form>
  );
}
function GrowthEditor({
  busy,
  onClose,
  onSave,
}: {
  busy: boolean;
  onClose: () => void;
  onSave: (value: unknown) => Promise<void>;
}) {
  const { t } = useI18n();
  const [note, setNote] = useState(""),
    [health, setHealth] = useState("Buona"),
    [height, setHeight] = useState(""),
    [paths, setPaths] = useState<string[]>([]),
    [uploading, setUploading] = useState(false),
    [error, setError] = useState("");
  return (
    <Modal title={t("growth.title")} onClose={onClose}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void onSave({
            note,
            health,
            heightCM: height ? Number(height) : null,
            photoPaths: paths,
          }).catch((e) => setError(e.message));
        }}
      >
        <label>
          {t("growth.health")}
          <select value={health} onChange={(e) => setHealth(e.target.value)}>
            {healthStates.map((s) => (
              <option key={s} value={s}>{t(healthStateKeys[s])}</option>
            ))}
          </select>
        </label>
        <label>
          {t("growth.height")}
          <input
            type="number"
            min={0}
            max={10000}
            step=".1"
            value={height}
            onChange={(e) => setHeight(e.target.value)}
          />
        </label>
        <label>
          {t("growth.note")}
          <textarea
            rows={4}
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
        </label>
        <label className="file-label">
          <ImagePlus size={20} />
          {uploading ? t("common.loading") : t("growth.photos")}
          <input
            type="file"
            multiple
            accept="image/jpeg,image/png,image/webp"
            disabled={uploading}
            onChange={async (e) => {
              const files = Array.from(e.target.files || []);
              setUploading(true);
              try {
                for (const file of files) {
                  const data = new FormData();
                  data.append("file", file);
                  const p = await api<{ path: string }>("photos", {
                    method: "POST",
                    body: data,
                  });
                  setPaths((old) => [...old, p.path]);
                }
              } catch (e) {
                setError((e as Error).message);
              } finally {
                setUploading(false);
              }
            }}
          />
        </label>
        <div className="growth-photos">
          {paths.map((p) => (
            <img key={p} src={photoURL(p, true)} alt={t("growth.photoAlt")} />
          ))}
        </div>
        {error && <p className="form-error">{error}</p>}
        <div className="modal-actions">
          <button type="button" className="button secondary" onClick={onClose}>
            {t("common.cancel")}
          </button>
          <button className="button primary" disabled={busy || uploading}>
            {t("growth.save")}
          </button>
        </div>
      </form>
    </Modal>
  );
}
function BackupTool({
  plants,
  run,
}: {
  plants: Plant[];
  run: (fn: () => Promise<unknown>, message?: string) => Promise<void>;
}) {
  const [file, setFile] = useState<File>(),
    [preview, setPreview] = useState<{
      format: string;
      counts: Record<string, number>;
      photos: number;
      measurements: number;
      missingPhotos: string[];
    }>(),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const inspect = async (f?: File) => {
    setFile(f);
    setPreview(undefined);
    setError("");
    if (!f) return;
    setBusy(true);
    const body = new FormData();
    body.append("file", f);
    try {
      setPreview(await api("import/preview", { method: "POST", body }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <section className="panel">
      <h2>Le tue piante, al sicuro.</h2>
      <p className="muted">
        Importa una volta il backup PlantCare nativo o ripristina un backup web
        su un archivio vuoto.
      </p>
      <label className="import-drop">
        <Upload size={27} />
        <strong>{file?.name || "Scegli un backup PlantCare"}</strong>
        <small>JSON nativo fino a 150 MB o ZIP web fino a 2 GB</small>
        <input
          type="file"
          accept="application/json,application/zip,.json,.zip"
          disabled={busy}
          onChange={(e) => void inspect(e.target.files?.[0])}
        />
      </label>
      {busy && (
        <p>
          <LoaderCircle className="spin" size={17} /> Verifico l’archivio…
        </p>
      )}
      {preview && (
        <div className="import-preview">
          <h3>{preview.format}</h3>
          <div className="import-counts">
            {Object.entries(preview.counts).map(([k, n]) => (
              <span key={k}>
                <b>{n}</b>
                {(
                  {
                    plants: "Piante",
                    fertilizers: "Prodotti",
                    speciesBiologies: "Specie",
                    recommendations: "Raccomandazioni",
                    proposals: "Proposte",
                  } as Record<string, string>
                )[k] || k}
              </span>
            ))}
            <span>
              <b>{preview.photos}</b>Fotografie
            </span>
          </div>
          {preview.missingPhotos.length > 0 && (
            <p className="danger">
              {preview.missingPhotos.length} fotografie non sono incluse nel
              backup originale. I riferimenti saranno conservati.
            </p>
          )}
          <button
            className="button primary"
            disabled={busy || plants.length > 0}
            onClick={async () => {
              if (!file) return;
              setBusy(true);
              const body = new FormData();
              body.append("file", file);
              try {
                await run(
                  () => api("import", { method: "POST", body }),
                  "Archivio importato",
                );
                setPreview(undefined);
                setFile(undefined);
              } catch (e) {
                setError((e as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            Importa questo archivio
          </button>
          {plants.length > 0 && (
            <p className="muted">
              L’archivio contiene già piante: l’importazione richiede un
              archivio vuoto.
            </p>
          )}
        </div>
      )}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      <hr />
      <h3>Esporta un backup</h3>
      <p className="muted">
        Per archivi grandi usa il backup Home Assistant e un backup separato
        della cartella delle fotografie. Il backup ZIP include i file senza
        convertirli in testo e viene preparato su disco.
      </p>
      <a className="button secondary" href="api/backup" download>
        <Download size={17} />
        Scarica backup ZIP completo
      </a>
    </section>
  );
}
function SettingsTool({ settings }: { settings: Settings }) {
  const { t, plural, preference, setPreference, formatNumber, formatDate } = useI18n();
  const [storage, setStorage] = useState<{
      photoDirectory: string;
      photos: number;
      photoBytes: number;
      databaseBytes: number;
      freeBytes: number;
      shared: boolean;
    }>(),
    [error, setError] = useState("");
  useEffect(() => {
    api<typeof storage>("storage")
      .then(setStorage)
      .catch((e) => setError(e.message));
  }, []);
  const size = (n: number) =>
    formatNumber(n / (1024 * 1024), { maximumFractionDigits: 1 }) + " MB";
  return (
    <section className="panel">
      <h2>{t("settings.title")}</h2>
      <p className="muted">{t("settings.description")}</p>
      <dl className="settings-list">
        <div>
          <dt>{t("settings.language")}</dt>
          <dd>
            <select
              aria-label={t("settings.language")}
              value={preference}
              onChange={(e) => setPreference(e.target.value as LanguagePreference)}
            >
              <option value="auto">{t("settings.languageAuto")}</option>
              <option value="it">{t("settings.languageIt")}</option>
              <option value="en">{t("settings.languageEn")}</option>
            </select>
            <small className="muted">{t("settings.languageHint")}</small>
          </dd>
        </div>
        <div>
          <dt>{t("settings.version")}</dt>
          <dd>{settings.version}</dd>
        </div>
        <div>
          <dt>{t("settings.timezone")}</dt>
          <dd>{settings.timezone}</dd>
        </div>
        <div>
          <dt>{t("settings.ai")}</dt>
          <dd>
            {settings.aiConfigured
              ? `${settings.aiProvider} · ${settings.aiModel}`
              : t("settings.aiNotConfigured")}
          </dd>
        </div>
        <div>
          <dt>{t("settings.autoApply")}</dt>
          <dd>{settings.autoApplyAI ? t("settings.enabled") : t("settings.disabled")}</dd>
        </div>
        <div>
          <dt>{t("settings.retention")}</dt>
          <dd>{plural("settings.days", settings.measurementRetentionDays)}</dd>
        </div>
        {settings.adaptiveStatus && <div><dt>{t("settings.weather")}</dt><dd>{settings.adaptiveStatus.errors ? plural("settings.weatherErrors", settings.adaptiveStatus.errors) : t("settings.lastRun", { date: formatDate(settings.adaptiveStatus.lastRun, { dateStyle: "short", timeStyle: "short" }) })}</dd></div>}
        {storage && (
          <>
            <div>
              <dt>{t("settings.database")}</dt>
              <dd>{size(storage.databaseBytes)}</dd>
            </div>
            <div>
              <dt>{t("settings.photos")}</dt>
              <dd>
                {formatNumber(storage.photos)} · {size(storage.photoBytes)}
              </dd>
            </div>
            <div>
              <dt>{t("settings.freeSpace")}</dt>
              <dd>{size(storage.freeBytes)}</dd>
            </div>
            <div>
              <dt>{t("settings.photoFolder")}</dt>
              <dd>
                <code>{storage.photoDirectory}</code>
              </dd>
            </div>
          </>
        )}
      </dl>
      <div className="info-note">
        <CircleHelp size={20} />
        <p>{t("settings.sharedNote")}</p>
      </div>
      {error && <p className="form-error">{error}</p>}
    </section>
  );
}
function SensorsTool({
  plants,
  settings,
  run,
}: {
  plants: Plant[];
  settings?: Settings;
  run: (fn: () => Promise<unknown>, message?: string) => Promise<void>;
}) {
  const [sensors, setSensors] = useState<Sensor[]>([]),
    [mappings, setMappings] = useState<Mapping[]>([]),
    [entity, setEntity] = useState(""),
    [target, setTarget] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    Promise.all([api<Sensor[]>("sensors"), api<Mapping[]>("sensor-mappings")])
      .then(([s, m]) => {
        setSensors(s);
        setMappings(m);
      })
      .catch((e) => setError(e.message));
  }, []);
  const rooms = [...new Set(plants.map((p) => p.room))];
  const save = async (next: Mapping[]) => {
    setBusy(true);
    try {
      await run(
        () =>
          api("sensor-mappings", { method: "PUT", body: JSON.stringify(next) }),
        "Associazioni salvate",
      );
      setMappings(next);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <section className="panel">
      <div className="section-heading">
        <h2>Sensori di casa</h2>
        <button
          className="button secondary"
          disabled={busy || !settings?.sensorsConfigured}
          onClick={() => {
            setBusy(true);
            void run(
              () => api("sensors/poll", { method: "POST" }),
              "Sensori aggiornati",
            )
              .catch((e) => setError(e.message))
              .finally(() => setBusy(false));
          }}
        >
          <RotateCw size={16} />
          Aggiorna
        </button>
      </div>
      <p className="muted">
        Autorizza le entità in <code>exposed_entities</code> nelle opzioni
        dell’add-on. Sono ammesse temperatura, umidità, luce, umidità terreno e
        conducibilità.
      </p>
      {!settings?.sensorsConfigured && (
        <p className="info-note">
          Il collegamento ai sensori sarà disponibile eseguendo l’add-on su Home
          Assistant.
        </p>
      )}
      {sensors.map((s) => (
        <div className="sensor-line" key={s.entityID}>
          <Thermometer size={18} />
          <span>
            <strong>{s.name}</strong>
            <small>{s.entityID}</small>
          </span>
          <b>
            {s.value.toLocaleString("it-IT", { maximumFractionDigits: 1 })}{" "}
            {s.unit}
          </b>
        </div>
      ))}
      <form
        className="mapping-form"
        onSubmit={(e) => {
          e.preventDefault();
          const next = [
            ...mappings,
            {
              entityID: entity,
              ...(target.startsWith("room:")
                ? { room: target.slice(5) }
                : { plantID: target }),
            },
          ];
          void save(next);
        }}
      >
        <label>
          Sensore
          <select
            required
            value={entity}
            onChange={(e) => setEntity(e.target.value)}
          >
            <option value="">Scegli un sensore</option>
            {sensors.map((s) => (
              <option key={s.entityID} value={s.entityID}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Associa a
          <select
            required
            value={target}
            onChange={(e) => setTarget(e.target.value)}
          >
            <option value="">Pianta o ambiente</option>
            <optgroup label="Piante">
              {plants.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </optgroup>
            <optgroup label="Ambienti">
              {rooms.map((r) => (
                <option key={r} value={"room:" + r}>
                  {r}
                </option>
              ))}
            </optgroup>
          </select>
        </label>
        <button
          className="button primary"
          disabled={busy || !entity || !target}
        >
          <Plus size={16} />
          Associa
        </button>
      </form>
      {mappings.map((m, i) => (
        <div className="mapping-line" key={i}>
          <span>
            {m.entityID}
            <small>
              {m.room ||
                plants.find((p) => p.id === m.plantID)?.name ||
                "Pianta non disponibile"}
            </small>
          </span>
          <button
            className="icon-button danger"
            aria-label="Rimuovi associazione"
            disabled={busy}
            onClick={() => void save(mappings.filter((_, j) => i !== j))}
          >
            <Trash2 size={16} />
          </button>
        </div>
      ))}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <I18nProvider>
      <App />
    </I18nProvider>
  </React.StrictMode>,
);

function ArchivePagination({label,page,size,total,onPage}:{label:string;page:number;size:number;total:number;onPage:(page:number)=>void}){
 const {t}=useI18n();
 if(total<=size)return null;
 return <nav className="archive-pagination" aria-label={label}><p className="muted small-text">{t("common.range",{from:(page-1)*size+1,to:Math.min(page*size,total),total})}</p><div className="button-row"><button className="button secondary" disabled={page===1} onClick={()=>onPage(page-1)}>{t("common.previous")}</button><button className="button secondary" disabled={page*size>=total} onClick={()=>onPage(page+1)}>{t("common.next")}</button></div></nav>;
}
