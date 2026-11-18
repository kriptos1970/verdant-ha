export type Action = {
  id: string;
  plantID: string;
  plantName: string;
  room: string;
  kind: string;
  dueDate: string;
  daysUntil: number;
  intervalDays: number;
  treatmentPlanID?: string;
  productID?: string;
  applicationNumber?: number;
  reason?: string;
  includesFertilizing?: boolean;
  canIncludeFertilizing?: boolean;
};
export type TrashItem = {
  id: string;
  name: string;
  species: string;
  room: string;
  photoPath?: string | null;
  deletedAt: string;
  expiresAt: string;
  daysLeft: number;
  _version: number;
};

export type PropertyLevel =
  | "veryLow"
  | "low"
  | "moderate"
  | "high"
  | "veryHigh"
  | "unknown";

export type DrainageQuality = "poor" | "moderate" | "good" | "excellent" | "unknown";

export type PlantSetup = {
  container?: {
    material?: string | null;
    diameterCM?: number | null;
    heightCM?: number | null;
    volumeLiters?: number | null;
    drainageHoles?: boolean | null;
    drainageQuality?: DrainageQuality;
    hasCachepot?: boolean | null;
    hasSaucer?: boolean | null;
  } | null;
  substrate?: {
    displayName?: string | null;
    commercialProductName?: string | null;
    components?: unknown[];
    properties?: {
      waterRetention?: PropertyLevel;
      drainage?: PropertyLevel;
      aeration?: PropertyLevel;
      organicContent?: PropertyLevel;
      compactionRisk?: PropertyLevel;
      pH?: number | null;
      ecMicrosiemensPerCM?: number | null;
    };
    propertyConfidence?: number;
    propertySource?: string;
  } | null;
  recordedAt?: string;
  modelVersion?: number;
};

export type CareEvent = {
  id: string;
  kind: string;
  date: string;
  note?: string;
  health?: string | null;
  status?: string;
  deletedAt?: string;
  postponedUntil?: string;
  treatmentPlanID?: string | null;
  productID?: string | null;
  applicationNumber?: number;
};
export type Growth = {
  id: string;
  date: string;
  note: string;
  health: string;
  photoPaths: string[];
  heightCM?: number;
};
export type PhotoAnnotation = {id:string;x:number;y:number;note:string};
export type HealthPhoto = {id:string;angle:string;path:string;annotations:PhotoAnnotation[]};
export type HealthSession = {id:string;date:string;health:string;note:string;photos:HealthPhoto[]};
export type Plant = {
  id: string;
  name: string;
  species: string;
  room: string;
  category: string;
  light: string;
  wateringInterval: number;
  fertilizingInterval?: number | null;
  rotationInterval?: number | null;
  inspectionInterval?: number | null;
  repottingInterval?: number | null;
  pruningInterval?: number | null;
  progressInterval?: number | null;
  acquiredOn: string;
  lastWatered: string;
  notes: string;
  photoPath?: string | null;
  catalogImageURL?: string;
  catalogImageAttribution?: string;
  carePlanMode?: string | null;
  history: CareEvent[];
  growthEntries?: Growth[];
  healthPhotoSessions?: HealthSession[];
  fertilizerProductID?: string | null;
  fertilizerDose?: string;
  fertilizerType?: string | null;
  lastFertilized?: string | null;
  plantingMethod?: string | null;
  careFrequencyPreference?: string | null;
  setup?: PlantSetup | null;
  potMaterial?: string;
  potDiameterCM?: number;
  heightCM?: number;
  potHasDrainage?: boolean;
  family?: string;
  adaptivePlan?: import("./adaptive").AdaptivePlan;
  careEngineApplied?: {
    fingerprint: string;
    appliedAt: string;
    previousDue: string;
    newDue: string;
    reason: string;
    measurementID?: string | null;
    moisturePercent?: number;
    confidence?: number;
  } | null;
  safetyProfile?: {
    poisonousToPets?: boolean;
    poisonousToHumans?: boolean;
    sourceName: string;
    sourceURL: string;
    fetchedAt?: string;
  };
  _summary?: boolean;
  _careCount?: number;
  _version: number;
  _schedule: Action[];
  _actions: Action[];
  treatmentPlans?: Treatment[];
  _treatments: Treatment[];
  _learning?: {
    explanation: string;
    confidence: number;
    learnedIntervalDays: number;
  };
};
export type Product = {
  id: string;
  name: string;
  brand: string;
  notes: string;
  applicationIntervalDays?: number | null;
  dosage?: string;
  form?: string;
  category?: string | null;
  applicationMethod?: string;
  suitableFor?: string;
  photoPath?: string;
  purchasedOn?: string | null;
  expiresOn?: string | null;
  _version: number;
};
export type Proposal = {
  id: string;
  plantID: string;
  plantName: string;
  currentWateringDays: number;
  proposedWateringDays: number;
  currentFertilizingDays?: number;
  proposedFertilizingDays: number;
  reason: string;
  stale: boolean;
  provider: string;
  model: string;
};
export type LocationMatch = {
  name: string;
  detail?: string;
  latitude: number;
  longitude: number;
};
export type Settings = {
  version: string;
  ingress?:boolean;
  services?: {plantnet:boolean;perenual:boolean;openplantbook?:boolean};
  timezone: string;
  location?: LocationMatch | null;
  aiProvider: string;
  aiModel: string;
  aiConfigured: boolean;
  autoApplyAI: boolean;
  aiUpdateTime: string;
  photoDirectory: string;
  sensorsConfigured: boolean;
  exposedEntities: string[];
  sensorStatus?: { error?: string; lastRun?: string };
  aiStatus?: { summary: string; lastRun: string; notificationError?:string };
  adaptiveStatus?: {lastRun:string;updated:number;errors:number};
  measurementRetentionDays: number;
  careEngineMode?: "shadow" | "active";
};
export type Mapping = {
  entityID: string;
  plantID?: string | null;
  room?: string | null;
};
export type Sensor = {
  entityID: string;
  name: string;
  kind: string;
  value: number;
  unit: string;
  updatedAt: string;
};
export type Measure = {
  id: number | string;
  kind: string;
  value: number;
  unit: string;
  measured_at: string;
  source_at?: string;
  entity_id: string;
  source?: string;
  reliability?: number | null;
};

export type Treatment = {
  id: string;
  productID: string;
  productName: string;
  startDate: string;
  intervalDays: number;
  totalApplications: number;
  completedApplications: number;
  endDate?: string | null;
  dose: string;
  notes: string;
  cancelledAt?: string | null;
  status: "active" | "complete" | "ended" | "cancelled";
  remainingApplications: number;
  nextDueDate?: string | null;
  calculatedEnd: string;
};
export type TreatmentDraft = Pick<
  Treatment,
  | "id"
  | "productID"
  | "startDate"
  | "intervalDays"
  | "totalApplications"
  | "endDate"
  | "dose"
  | "notes"
>;
export type CareSelection = {
  plant: Plant;
  kind: string;
  event?: CareEvent;
  scheduled?: Action;
  postponed?: boolean;
};
