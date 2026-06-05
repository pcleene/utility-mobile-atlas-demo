export function formatMYR(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  return new Intl.NumberFormat('en-MY', {
    style: 'currency',
    currency: 'MYR',
    currencyDisplay: 'narrowSymbol',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(n);
}

export function formatRMUnit(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  return `RM ${n.toFixed(2)}`;
}

export function formatKWh(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return '— kWh';
  return `${n.toFixed(n >= 100 ? 0 : 1)} kWh`;
}

export function formatDate(iso: string | null | undefined, opts?: Intl.DateTimeFormatOptions): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString('en-MY', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    ...opts
  });
}

export function formatRelative(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86_400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 86_400 * 7) return `${Math.floor(diff / 86_400)}d ago`;
  return formatDate(iso);
}

export function maskAccountNo(no: string | null | undefined): string {
  if (!no) return '—';
  const tail = no.slice(-4);
  return `••• ${tail}`;
}

export function timeOfDayGreeting(now = new Date()): { en: string; bm: string } {
  const h = now.getHours();
  if (h < 12) return { en: 'Good morning', bm: 'Selamat pagi' };
  if (h < 15) return { en: 'Good afternoon', bm: 'Selamat tengah hari' };
  if (h < 19) return { en: 'Good evening', bm: 'Selamat petang' };
  return { en: 'Good evening', bm: 'Selamat malam' };
}

export function isPeakNow(now = new Date()): boolean {
  const h = now.getHours();
  const wd = now.getDay();
  return wd >= 1 && wd <= 5 && h >= 14 && h < 22;
}
