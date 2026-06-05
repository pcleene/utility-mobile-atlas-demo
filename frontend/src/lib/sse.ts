import { browser } from '$app/environment';
import { PUBLIC_API_BASE_URL } from '$env/static/public';
import { toasts } from './stores.svelte';
import type { NotificationEvent } from './types';

let _es: EventSource | null = null;
let _retry = 0;

export function connectNotificationStream(): void {
  if (!browser || _es) return;
  const url = `${PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1'}/events/stream`;
  try {
    _es = new EventSource(url);
  } catch {
    return;
  }
  _es.addEventListener('notification', (ev: MessageEvent) => {
    try {
      const payload = JSON.parse(ev.data) as NotificationEvent;
      toasts.push(payload);
    } catch {
      /* ignore malformed frame */
    }
  });
  _es.onerror = () => {
    _es?.close();
    _es = null;
    _retry = Math.min(_retry + 1, 5);
    setTimeout(connectNotificationStream, 1000 * _retry);
  };
}

export function disconnectNotificationStream(): void {
  _es?.close();
  _es = null;
}
