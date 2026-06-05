<script lang="ts">
  import type { Bill } from '$lib/types';
  import { formatMYR } from '$lib/format';
  import { CheckCircle2, X } from '@lucide/svelte';

  let {
    bill,
    open = false,
    onClose
  }: {
    bill: Bill | null;
    open: boolean;
    onClose: () => void;
  } = $props();

  let stage = $state<'confirm' | 'success'>('confirm');
  let processing = $state(false);

  $effect(() => {
    if (!open) {
      stage = 'confirm';
      processing = false;
    }
  });

  async function pay() {
    processing = true;
    await new Promise((r) => setTimeout(r, 900));
    stage = 'success';
    processing = false;
    setTimeout(onClose, 1400);
  }
</script>

{#if open && bill}
  <div
    class="sheet-backdrop"
    role="presentation"
    onclick={onClose}
    onkeydown={(e) => e.key === 'Escape' && onClose()}
  ></div>
  <div class="sheet" role="dialog" aria-modal="true" aria-label="Pay bill">
    <div class="mx-auto h-1.5 w-10 rounded-full bg-ink-100"></div>

    {#if stage === 'confirm'}
      <div class="mt-3 flex items-center justify-between">
        <h3 class="text-[17px] font-semibold">Confirm payment</h3>
        <button
          class="grid h-8 w-8 place-items-center rounded-full text-ink-500 active:bg-ink-100"
          aria-label="Close"
          onclick={onClose}
        >
          <X size={18} />
        </button>
      </div>

      <div class="mt-4 space-y-2 rounded-2xl bg-bg p-4">
        <div class="flex justify-between text-[13px] text-ink-700">
          <span>Account</span>
          <span class="font-medium">••• {bill.account_no.slice(-4)}</span>
        </div>
        <div class="flex justify-between text-[13px] text-ink-700">
          <span>Bill</span>
          <span class="font-medium">{bill.bill_no}</span>
        </div>
        <div class="flex justify-between text-[13px] text-ink-700">
          <span>Method</span>
          <span class="font-medium">JomPAY · 8881</span>
        </div>
        <div
          class="flex items-end justify-between border-t border-ink-100 pt-3 text-ink-900"
        >
          <span class="text-[13px] text-ink-500">Total</span>
          <span class="tnum text-[24px] font-bold">{formatMYR(bill.total_myr)}</span>
        </div>
      </div>

      <button class="btn-primary mt-5" onclick={pay} disabled={processing}>
        {processing ? 'Processing…' : `Pay ${formatMYR(bill.total_myr)}`}
      </button>
      <button class="btn-secondary mt-2" onclick={onClose} disabled={processing}>
        Cancel
      </button>
    {:else}
      <div class="flex flex-col items-center pt-4 pb-2">
        <div
          class="grid h-16 w-16 place-items-center rounded-full bg-success-soft text-success"
        >
          <CheckCircle2 size={36} strokeWidth={2.4} />
        </div>
        <h3 class="mt-3 text-[18px] font-semibold">Payment received</h3>
        <p class="text-center text-[13px] text-ink-500">
          We've recorded your payment of {formatMYR(bill.total_myr)}.
        </p>
      </div>
    {/if}
  </div>
{/if}
