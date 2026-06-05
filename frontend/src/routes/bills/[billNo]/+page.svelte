<script lang="ts">
  import { page } from '$app/stores';
  import AppBar from '$lib/components/AppBar.svelte';
  import Skeleton from '$lib/components/Skeleton.svelte';
  import StatusPill from '$lib/components/StatusPill.svelte';
  import PaySheet from '$lib/components/PaySheet.svelte';
  import InspectOverlay from '$lib/components/InspectOverlay.svelte';
  import { api } from '$lib/api';
  import { formatDate, formatMYR } from '$lib/format';
  import type { Bill, BillLine, MongoInspect } from '$lib/types';
  import { Download } from '@lucide/svelte';

  let bill = $state<Bill | null>(null);
  let inspectBill = $state<MongoInspect | null>(null);
  let loading = $state(true);
  let showPay = $state(false);

  $effect(() => {
    const billNo = $page.params.billNo;
    if (!billNo) return;
    void load(billNo);
  });

  async function load(billNo: string): Promise<void> {
    loading = true;
    try {
      const res = await api.bill(billNo);
      bill = res.data;
      inspectBill = res.inspect ?? null;
    } catch {
      bill = null;
      inspectBill = null;
    } finally {
      loading = false;
    }
  }

  function lines(b: Bill): BillLine[] {
    const out: BillLine[] = [b.breakdown.energy];
    if (b.breakdown.energy_offpeak) out.push(b.breakdown.energy_offpeak);
    out.push(b.breakdown.capacity, b.breakdown.network, b.breakdown.retail, b.breakdown.afa);
    return out;
  }
</script>

<AppBar title="Bill detail" showBack />

<div class="px-5 pt-2 pb-6">
  {#if loading}
    <div class="space-y-3">
      <Skeleton height="120px" rounded="20px" />
      <Skeleton height="240px" rounded="20px" />
    </div>
  {:else if !bill}
    <div class="card p-6 text-center text-[14px] text-ink-500">
      Bill not found.
    </div>
  {:else}
    <InspectOverlay inspect={inspectBill}>
    <!-- Header -->
    <div class="card p-5">
      <div class="flex items-center justify-between">
        <div>
          <div class="text-[12px] text-ink-500">
            {formatDate(bill.billing_period_start, { day: '2-digit', month: 'short' })}
            – {formatDate(bill.billing_period_end, { day: '2-digit', month: 'short', year: 'numeric' })}
          </div>
          <div class="mt-0.5 text-[13px] font-mono text-ink-700">
            {bill.bill_no}
          </div>
        </div>
        <StatusPill status={bill.status} overdueDays={bill.days_until_due} />
      </div>
      <div class="mt-3 grid grid-cols-3 gap-2 text-[12px]">
        <div class="rounded-md bg-ink-100/60 px-3 py-2">
          <div class="text-ink-500">Total</div>
          <div class="tnum font-bold">{bill.total_kwh.toFixed(1)} kWh</div>
        </div>
        {#if bill.peak_kwh != null}
          <div class="rounded-md bg-ink-100/60 px-3 py-2">
            <div class="text-ink-500">Peak</div>
            <div class="tnum font-bold">{bill.peak_kwh.toFixed(1)} kWh</div>
          </div>
        {/if}
        {#if bill.offpeak_kwh != null}
          <div class="rounded-md bg-ink-100/60 px-3 py-2">
            <div class="text-ink-500">Off-peak</div>
            <div class="tnum font-bold">{bill.offpeak_kwh.toFixed(1)} kWh</div>
          </div>
        {/if}
      </div>
    </div>

    <!-- Itemised breakdown -->
    <h2
      class="mt-5 mb-2 text-[12px] font-semibold tracking-widest text-ink-500 uppercase"
    >
      Breakdown (RP4 tariff)
    </h2>
    <div class="card divide-y divide-ink-100 p-0">
      {#each lines(bill) as l (l.code)}
        <div class="flex items-start justify-between p-4">
          <div class="min-w-0 flex-1 pr-3">
            <div class="text-[14px] font-semibold text-ink-900">{l.label}</div>
            <div class="text-[12px] leading-snug text-ink-500">{l.detail}</div>
          </div>
          <div
            class="tnum text-[14px] font-bold"
            class:text-success={l.amount_myr < 0}
          >
            {formatMYR(l.amount_myr)}
          </div>
        </div>
      {/each}
    </div>

    {#if bill.breakdown.waivers.length > 0 || bill.breakdown.incentives.length > 0}
      <h2
        class="mt-5 mb-2 text-[12px] font-semibold tracking-widest text-ink-500 uppercase"
      >
        Incentives & waivers
      </h2>
      <div class="card divide-y divide-ink-100 p-0">
        {#each [...bill.breakdown.incentives, ...bill.breakdown.waivers] as l (l.code)}
          <div class="flex items-start justify-between p-4">
            <div class="min-w-0 flex-1 pr-3">
              <div class="text-[14px] font-semibold text-ink-900">{l.label}</div>
              <div class="text-[12px] leading-snug text-ink-500">{l.detail}</div>
            </div>
            <div class="tnum text-[14px] font-bold text-success">
              {formatMYR(l.amount_myr)}
            </div>
          </div>
        {/each}
      </div>
    {/if}

    <!-- Total -->
    <div class="card mt-5 p-5">
      <div class="flex justify-between text-[13px] text-ink-500">
        <span>Subtotal</span>
        <span class="tnum">{formatMYR(bill.subtotal_myr)}</span>
      </div>
      {#if bill.rounding_myr !== 0}
        <div class="mt-1 flex justify-between text-[13px] text-ink-500">
          <span>Rounding adjustment</span>
          <span class="tnum">{formatMYR(bill.rounding_myr)}</span>
        </div>
      {/if}
      <div
        class="mt-3 flex items-end justify-between border-t border-ink-100 pt-3"
      >
        <span class="text-[13px] text-ink-500">Total payable</span>
        <span class="tnum text-[28px] leading-none font-bold">
          {formatMYR(bill.total_myr)}
        </span>
      </div>
      <div class="mt-1 text-right text-[12px] text-ink-500">
        Due {formatDate(bill.due_at)}
      </div>

      <div class="mt-4 flex gap-2">
        {#if bill.status !== 'PAID'}
          <button class="btn-primary" onclick={() => (showPay = true)}
            >Pay Now</button
          >
        {/if}
        <button class="btn-secondary">
          <Download size={16} class="mr-1.5" /> Download PDF
        </button>
      </div>
    </div>
    </InspectOverlay>
  {/if}
</div>

<PaySheet bill={bill} open={showPay} onClose={() => (showPay = false)} />
