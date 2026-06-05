import type { MongoInspect } from './types';

/** Static inspect payloads for client-only UI (no Mongo round-trip). */
export function staticInspect(
  title: string,
  note: string,
  features: string[] = ['Client-side']
): MongoInspect {
  return {
    title,
    collection: '—',
    operation: 'client',
    features,
    endpoint: '(browser)',
    sample_documents: [],
    note
  };
}

export const STATIC_INSPECT = {
  timeBanner: staticInspect(
    'Peak / off-peak banner',
    'Derived in the browser from local clock — weekday 14:00–22:00 = peak. No MongoDB query.',
    ['Time-of-use logic', 'Client-side']
  ),
  quickActions: staticInspect(
    'Quick actions grid',
    'Static navigation tiles — not backed by a MongoDB collection in this prototype.',
    ['UI only']
  ),
  promos: staticInspect(
    'Promotions strip',
    'Hard-coded promo cards for visual polish. A production app would read from a `promotions` collection with TTL.',
    ['UI only']
  ),
  paySheet: staticInspect(
    'Pay Now confirmation',
    'Simulated payment flow — no write to MongoDB in the prototype (would insert into `transactions` in production).',
    ['UI only']
  ),
  sse: staticInspect(
    'Live notifications (SSE)',
    'FastAPI tails MongoDB change streams on `bills` (insert), `outages` (update), and `notifications` (insert), then pushes events over Server-Sent Events.',
    ['Change Streams', 'SSE']
  ),
  profile: staticInspect(
    'Profile & settings',
    'Customer document loaded once at boot via GET /customers/me and held in Svelte session state.',
    ['Document model', 'Session cache']
  )
} as const;
