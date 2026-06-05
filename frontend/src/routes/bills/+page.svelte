<script lang="ts">
  import AppBar from '$lib/components/AppBar.svelte';
  import Skeleton from '$lib/components/Skeleton.svelte';
  import StatusPill from '$lib/components/StatusPill.svelte';
  import InspectOverlay from '$lib/components/InspectOverlay.svelte';
  import { api } from '$lib/api';
  import { session } from '$lib/stores.svelte';
  import { formatDate, formatMYR } from '$lib/format';
  import { ChevronRight, Receipt } from '@lucide/svelte';
  import { goto } from '$app/navigation';
  import type { Bill, BillStatus, MongoInspect } from '$lib/types';

  type Filter = 'ALL' | BillStatus;
  let filter = $state<Filter>('ALL');
  let bills = $state<Bill[]>([]);
  let inspectBills = $state<MongoInspect | null>(null);
  let loading = $state(true);

  $effect(() => {
    const acc = session.selectedAccount;
    if (!acc) return;
    void load(acc.account_no, filter);
  });

  async function load(no: string, f: Filter): Promise<void> {
    loading = true;
    try {
      const res = await api.bills(no, f);
      bills = res.data;
      inspectBills = res.inspect ?? null;
    } catch {
      bills = [];
      inspectBills = null;
    } finally {
      loading = false;
    }
  }

  const filters: { id: Filter; label: string }[] = [
    { id: 'ALL', label: 'All' },
    { id: 'UNPAID', label: 'Unpaid' },
    { id: 'PAID', label: 'Paid' }
  ];
</script>

<AppBar title="Bills" />

<div class="px-5 pt-2 pb-6">
  <div class="mb-4 inline-flex rounded-full bg-ink-100 p-1">
    {#each filters as f (f.id)}
      <button
        class="px-4 py-1.5 text-[13px] font-semibold rounded-full transition-colors"
        class:bg-surface={filter === f.id}
        class:shadow-[0_1px_3px_rgba(15,17,22,0.08)]={filter === f.id}
        class:text-ink-900={filter === f.id}
        class:text-ink-500={filter !== f.id}
        onclick={() => (filter = f.id)}
      >
        {f.label}
      </button>
    {/each}
  </div>

  <InspectOverlay inspect={inspectBills}>
    <div class="space-y-3">
      {#if loading}
        {#each [0, 1, 2, 3] as _ (_)}
          <Skeleton height="80px" rounded="20px" />
        {/each}
      {:else if bills.length === 0}
        <div class="card flex flex-col items-center gap-3 p-8 text-center">
          <div
            class="grid h-12 w-12 place-items-center rounded-full bg-Utility-orange-soft text-Utility-orange-dark"
          >
            <Receipt size={20} />
          </div>
          <div class="text-[14px] font-semibold">No bills here yet</div>
          <div class="text-[12.5px] text-ink-500">
            Bills will appear once your billing cycle closes.
          </div>
        </div>
      {:else}
        {#each bills as b (b.bill_no)}
          <button
            class="card-press card flex w-full items-center gap-3 p-4 text-left"
            onclick={() => goto(`/bills/${b.bill_no}`)}
          >
            <div
              class="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-Utility-orange-soft text-Utility-orange-dark"
            >
              <Receipt size={18} />
            </div>
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <div class="text-[14px] font-semibold">
                  {new Date(b.billing_period_end).toLocaleDateString('en-MY', {
                    month: 'long',
                    year: 'numeric'
                  })}
                </div>
                <StatusPill status={b.status} overdueDays={b.days_until_due} />
              </div>
              <div class="text-[12px] text-ink-500">
                Due {formatDate(b.due_at)} · {b.total_kwh.toFixed(0)} kWh
              </div>
            </div>
            <div class="text-right">
              <div class="tnum text-[15px] font-bold">{formatMYR(b.total_myr)}</div>
            </div>
            <ChevronRight size={18} class="ml-1 text-ink-300" />
          </button>
        {/each}
      {/if}
    </div>
  </InspectOverlay>
</div>
