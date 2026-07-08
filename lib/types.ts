export type Severity = "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type FindingStatus = "PASS" | "WARNING" | "FAIL" | "NOT_APPLICABLE";

export type Finding = {
  ruleId: string;
  section: string;
  rule: string;
  severity: Severity;
  status: FindingStatus;
  finding: string;
  detectedValue: string;
  basis: string;
  recommendation: string;
  clarificationQuestion: string;
};

export type PriceLimit = {
  kbli: string;
  description: string;
  lower: number;
  upper: number;
  sourcePeriod: string;
};

export type PriceLimitMap = Record<string, PriceLimit>;

export type TableRow = Record<string, string>;

export type ReportSectionKey =
  | "identity"
  | "general"
  | "inventory"
  | "capacity"
  | "production"
  | "materials"
  | "helpers"
  | "investment"
  | "labor"
  | "internship"
  | "water"
  | "energy"
  | "expenses"
  | "productionPlan"
  | "machines"
  | "solidWaste"
  | "hazardousWaste"
  | "liquidWaste";

export type CapacityRow = {
  product: string;
  kbli: string;
  hs: string;
  productionOriginal: string;
  installedOriginal: string;
  productionKg: number;
  installedKg: number;
};

export type ProductionRow = {
  product: string;
  kbli: string;
  hs: string;
  unit: string;
  productionQty: number;
  productionKg: number;
  productionValue: number;
  salesQty: number;
  salesKg: number;
  salesValue: number;
  stockSoldFlag: boolean;
  exportPercent: number;
};

export type MaterialRow = {
  name: string;
  hs: string;
  unit: string;
  domesticQty: number;
  domesticKg: number;
  domesticValue: number;
  importQty: number;
  importKg: number;
  importValue: number;
  kbliProduct: string;
  productName: string;
  inventoryKg: number;
  inventoryValue: number;
};

export type InventoryRow = {
  type: string;
  startValue: number;
  endValue: number;
};

export type LaborSummary = {
  productionPermanentMale: number;
  productionTemporaryMale: number;
  otherPermanentMale: number;
  otherTemporaryMale: number;
  productionPermanentFemale: number;
  productionTemporaryFemale: number;
  otherPermanentFemale: number;
  otherTemporaryFemale: number;
  educationTotal: number;
  totalWorkers: number;
};

export type LiquidWaste = {
  inletDebit: number;
  outletDebit: number;
  codInlet: number;
  codOutlet: number;
  sludgeRemoved: number;
};

export type ParsedReport = {
  fileName: string;
  rawText: string;
  companyName: string;
  identity: Record<string, string>;
  general: Record<string, string>;
  sectionsText: Record<ReportSectionKey, string>;
  inventory: InventoryRow[];
  capacity: CapacityRow[];
  production: ProductionRow[];
  materials: MaterialRow[];
  helpers: MaterialRow[];
  labor: LaborSummary;
  waterRows: TableRow[];
  energyRows: TableRow[];
  expenses: Record<string, number | string>;
  productionPlanRows: TableRow[];
  machineRows: TableRow[];
  solidWasteRows: TableRow[];
  hazardousWasteRows: TableRow[];
  liquidWaste: LiquidWaste;
  parserWarnings: string[];
};

export type ValidationResult = {
  findings: Finding[];
  riskScore: number;
  recommendation: string;
  sectionSummaries: SectionSummary[];
};

export type SectionSummary = {
  key: ReportSectionKey;
  label: string;
  score: number;
  recommendation: string;
  counts: Record<Severity, number>;
  topFindings: Finding[];
};

