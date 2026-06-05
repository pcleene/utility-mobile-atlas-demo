import type { Account, Customer, MongoInspect, NotificationEvent } from './types';

/**
 * Cross-route state. Svelte 5 runes inside a `.svelte.ts` module — every
 * importer gets the same instance.
 *
 * Why a class wrapper: rune-backed primitives at the top of a module
 * can't be re-exported through `export const`. Wrapping them in a class
 * gives us reactivity *and* a stable named handle.
 */
class Session {
  customer = $state<Customer | null>(null);
  selectedAccountNo = $state<string | null>(null);
  hydrated = $state(false);

  selectedAccount = $derived<Account | null>(
    this.customer?.accounts.find((a) => a.account_no === this.selectedAccountNo) ??
      this.customer?.accounts[0] ??
      null
  );

  setCustomer(c: Customer): void {
    this.customer = c;
    if (!this.selectedAccountNo && c.accounts.length > 0) {
      this.selectedAccountNo = c.accounts[0].account_no;
    }
    this.hydrated = true;
  }

  selectAccount(no: string): void {
    this.selectedAccountNo = no;
  }
}

class Toasts {
  items = $state<(NotificationEvent & { id: string })[]>([]);
  push(n: NotificationEvent): void {
    const id = crypto.randomUUID();
    this.items = [...this.items, { ...n, id }];
    setTimeout(() => this.dismiss(id), 5000);
  }
  dismiss(id: string): void {
    this.items = this.items.filter((t) => t.id !== id);
  }
}

export const session = new Session();
export const toasts = new Toasts();

class MongoInspector {
  open = $state(false);
  payload = $state<MongoInspect | null>(null);

  show(inspect: MongoInspect | null | undefined): void {
    if (!inspect) return;
    this.payload = inspect;
    this.open = true;
  }

  close(): void {
    this.open = false;
  }
}

export const mongoInspector = new MongoInspector();
