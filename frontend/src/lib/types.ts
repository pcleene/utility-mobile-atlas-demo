export type Relationship = 'OWNER' | 'TENANT';
export type TariffScheme = 'GENERAL' | 'TOU';
export type CustomerClass = 'RESIDENTIAL' | 'COMMERCIAL';
export type BillStatus = 'PAID' | 'UNPAID' | 'OVERDUE';
export type OutageStatus = 'ACTIVE' | 'INVESTIGATING' | 'RESTORING' | 'RESOLVED';

export interface GeoPoint {
  type: 'Point';
  coordinates: [number, number];
}

export interface GeoPolygon {
  type: 'Polygon';
  coordinates: number[][][];
}

export interface Address {
  line1: string;
  line2?: string | null;
  city: string;
  state: string;
  postcode: string;
  country: string;
  location?: GeoPoint | null;
}

export interface Account {
  account_no: string;
  nickname: string;
  relationship: Relationship;
  tariff_scheme: TariffScheme;
  customer_class: CustomerClass;
  address: Address;
  meter_no: string;
  activated_at: string;
  last_bill_amount?: number | null;
  last_bill_status?: BillStatus | null;
}

export interface Customer {
  customer_id: string;
  name: string;
  salutation?: string | null;
  ic_masked: string;
  email: string;
  phone: string;
  primary_language: 'EN' | 'BM' | 'ZH';
  accounts: Account[];
  avatar_color: string;
}

export interface BillLine {
  label: string;
  detail: string;
  amount_myr: number;
  code: string;
}

export interface BillBreakdown {
  energy: BillLine;
  energy_offpeak?: BillLine | null;
  capacity: BillLine;
  network: BillLine;
  retail: BillLine;
  afa: BillLine;
  incentives: BillLine[];
  waivers: BillLine[];
}

export interface Bill {
  bill_no: string;
  account_no: string;
  customer_id: string;
  billing_period_start: string;
  billing_period_end: string;
  issued_at: string;
  due_at: string;
  status: BillStatus;
  paid_at?: string | null;
  total_kwh: number;
  peak_kwh?: number | null;
  offpeak_kwh?: number | null;
  breakdown: BillBreakdown;
  subtotal_myr: number;
  rounding_myr: number;
  total_myr: number;
  pdf_url?: string | null;
  days_until_due?: number | null;
}

export interface DailyUsage {
  date: string;
  total_kwh: number;
  peak_kwh: number;
  offpeak_kwh: number;
  estimated_cost_myr: number;
}

export interface MonthlyUsage {
  month: string;
  total_kwh: number;
  peak_kwh: number;
  offpeak_kwh: number;
  estimated_cost_myr: number;
}

export interface Insight {
  icon: 'trend-up' | 'trend-down' | 'lightbulb' | 'clock' | 'leaf';
  title: string;
  body: string;
  estimated_savings_myr?: number | null;
}

export interface OutageAffected {
  label: string;
  area: GeoPolygon;
  centroid: GeoPoint;
}

export interface Outage {
  outage_id: string;
  status: OutageStatus;
  cause: string;
  substation?: string | null;
  started_at: string;
  eta_restoration?: string | null;
  last_update: string;
  affected: OutageAffected;
  customers_affected: number;
}

export interface SupportHit {
  ticket_id: string;
  title: string;
  summary: string;
  category: string;
  lang: 'EN' | 'BM' | 'ZH';
  resolution_steps: string[];
  score: number;
  matched_via: 'lexical' | 'vector' | 'hybrid';
}

export interface SupportSearchResponse {
  hits: SupportHit[];
  engine: string;
}

export interface NotificationEvent {
  ts: string;
  type: string;
  title: string;
  body: string;
  data?: Record<string, unknown>;
}

/** Metadata returned when fetching with `X-Mongo-Inspect: 1`. */
export interface MongoInspect {
  title: string;
  collection: string;
  operation: string;
  features: string[];
  endpoint: string;
  filter?: Record<string, unknown> | null;
  pipeline?: Record<string, unknown>[] | null;
  sort?: Record<string, unknown> | unknown[] | null;
  limit?: number | null;
  index?: string | null;
  indexes?: string[];
  sample_documents: Record<string, unknown>[];
  note?: string | null;
  engine?: string | null;
}

export interface ApiResult<T> {
  data: T;
  inspect?: MongoInspect;
}
