<script lang="ts">
  import type { Bill } from '$lib/types';
  import { formatMYR, formatDate } from '$lib/format';
  import StatusPill from './StatusPill.svelte';
  import { goto } from '$app/navigation';
  import { Receipt } from '@lucide/svelte';

  let {
    bill,
    onPay
  }: {
    bill: Bill | null;
    onPay?: () => void;
  } = $props();

  const urgent = $derived(
    bill?.status === 'UNPAID' &&
      bill?.days_until_due != null &&
      bill.days_until_due <= 5
  );
</script>

{#if bill}
  <div
    class="card overflow-hidden p-5"
    style:border={urgent ? '1.5px solid var(--color-Utility-orange)' : undefined}
    style:box-shadow={urgent ? 'var(--shadow-pop)' : undefined}
  >
    <div class="flex items-start justify-between">
      <div>
        <div class="flex items-center gap-2 text-[12.5px] text-ink-500">
          <Receipt size={14} /> Current bill
        </div>
        <div class="tnum mt-1.5 text-[34px] font-bold leading-none text-ink-900">
          {formatMYR(bill.total_myr)}
        </div>
        <div class="mt-1.5 text-[12.5px] text-ink-500">
          Due {formatDate(bill.due_at)}
          {#if bill.days_until_due != null && bill.days_until_due >= 0 && bill.status === 'UNPAID'}
            <span class="text-ink-700">· in {bill.days_until_due} days</span>
          {/if}
        </div>
      </div>
      <StatusPill status={bill.status} overdueDays={bill.days_until_due} />
    </div>

    <div class="mt-4 grid grid-cols-2 gap-2 text-[12px]">
      <div class="rounded-md bg-ink-100/60 px-3 py-2">
        <div class="text-ink-500">Period</div>
        <div class="font-medium text-ink-700">
          {formatDate(bill.billing_period_start, { day: '2-digit', month: 'short' })} – {formatDate(bill.billing_period_end, { day: '2-digit', month: 'short' })}
        </div>
      </div>
      <div class="rounded-md bg-ink-100/60 px-3 py-2">
        <div class="text-ink-500">Usage</div>
        <div class="tnum font-medium text-ink-700">
          {bill.total_kwh.toFixed(0)} kWh
        </div>
      </div>
    </div>

    <div class="mt-4 flex gap-2">
      {#if bill.status !== 'PAID'}
        <button class="btn-primary" onclick={onPay}>Pay Now</button>
      {/if}
      <button
        class="btn-secondary"
        onclick={() => goto(`/bills/${bill.bill_no}`)}
      >
        Details
      </button>
    </div>
  </div>
{/if}
