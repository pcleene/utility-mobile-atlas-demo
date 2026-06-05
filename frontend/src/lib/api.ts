import { PUBLIC_API_BASE_URL } from '$env/static/public';
import type {
  Account,
  ApiResult,
  Bill,
  Customer,
  DailyUsage,
  Insight,
  MongoInspect,
  MonthlyUsage,
  Outage,
  SupportSearchResponse
} from './types';

const BASE = PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

const INSPECT_HEADERS = { 'X-Mongo-Inspect': '1' };

function unwrap<T>(body: unknown): ApiResult<T> {
  if (
    body &&
    typeof body === 'object' &&
    'data' in body &&
    '_inspect' in body
  ) {
    const wrapped = body as { data: T; _inspect: MongoInspect };
    return { data: wrapped.data, inspect: wrapped._inspect };
  }
  return { data: body as T };
}

async function jget<T>(path: string, init?: RequestInit): Promise<ApiResult<T>> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    credentials: 'omit',
    headers: { ...INSPECT_HEADERS, ...(init?.headers ?? {}) }
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API ${res.status}: ${text || path}`);
  }
  return unwrap<T>(await res.json());
}

async function jpost<T>(path: string, body: unknown): Promise<ApiResult<T>> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json', ...INSPECT_HEADERS },
    body: JSON.stringify(body)
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API ${res.status}: ${text || path}`);
  }
  return unwrap<T>(await res.json());
}

export const api = {
  base: BASE,

  me: () => jget<Customer>('/customers/me'),
  accounts: () => jget<Account[]>('/accounts'),
  account: (no: string) => jget<Account>(`/accounts/${encodeURIComponent(no)}`),

  bills: (accountNo: string, status: string = 'ALL') =>
    jget<Bill[]>(
      `/bills?accountNo=${encodeURIComponent(accountNo)}&status=${status}`
    ),
  bill: (billNo: string) => jget<Bill>(`/bills/${encodeURIComponent(billNo)}`),

  usageDaily: (accountNo: string, days = 30) =>
    jget<DailyUsage[]>(
      `/usage/${encodeURIComponent(accountNo)}/daily?days=${days}`
    ),
  usageMonthly: (accountNo: string, months = 12) =>
    jget<MonthlyUsage[]>(
      `/usage/${encodeURIComponent(accountNo)}/monthly?months=${months}`
    ),
  insights: (accountNo: string) =>
    jget<{ insights: Insight[] }>(
      `/usage/${encodeURIComponent(accountNo)}/insights`
    ),

  outages: () => jget<Outage[]>('/outages'),
  outagesNearby: (lng: number, lat: number) =>
    jget<Outage[]>(`/outages/nearby?lng=${lng}&lat=${lat}`),
  reportOutage: (body: {
    account_no: string;
    description: string;
    location: { type: 'Point'; coordinates: [number, number] };
    severity?: 'LOW' | 'MEDIUM' | 'HIGH';
    contact_phone?: string;
  }) => jpost<{ ok: boolean; notification_id?: string }>('/outages/report', body),

  supportSearch: (query: string, lang: 'EN' | 'BM' | 'ZH' = 'EN', topK = 10) =>
    jpost<SupportSearchResponse>('/support/search', {
      query,
      lang,
      top_k: topK
    }),

  cluster: () => jget<Record<string, unknown>>('/health/cluster')
};
