<script lang="ts">
  import AppBar from '$lib/components/AppBar.svelte';
  import Skeleton from '$lib/components/Skeleton.svelte';
  import StatusPill from '$lib/components/StatusPill.svelte';
  import MalaysiaMap from '$lib/components/MalaysiaMap.svelte';
  import InspectableSection from '$lib/components/InspectableSection.svelte';
  import InspectOverlay from '$lib/components/InspectOverlay.svelte';
  import { api } from '$lib/api';
  import { session } from '$lib/stores.svelte';
  import { formatRelative } from '$lib/format';
  import { Plus, MapPin, X } from '@lucide/svelte';
  import type { MongoInspect, Outage } from '$lib/types';

  let outages = $state<Outage[]>([]);
  let inspectOutages = $state<MongoInspect | null>(null);
  let inspectReport = $state<MongoInspect | null>(null);
  let loading = $state(true);
  let showReport = $state(false);
  let reportText = $state('');
  let submitting = $state(false);
  let submitted = $state(false);

  $effect(() => {
    void load();
  });

  async function load() {
    loading = true;
    try {
      const res = await api.outages();
      outages = res.data;
      inspectOutages = res.inspect ?? null;
    } catch {
      outages = [];
      inspectOutages = null;
    } finally {
      loading = false;
    }
  }

  async function submitReport() {
    const acc = session.selectedAccount;
    if (!acc?.address.location) return;
    submitting = true;
    try {
      const res = await api.reportOutage({
        account_no: acc.account_no,
        description: reportText.trim() || 'No power at supply point.',
        location: acc.address.location,
        severity: 'MEDIUM'
      });
      inspectReport = res.inspect ?? null;
      submitted = true;
      setTimeout(() => {
        showReport = false;
        submitted = false;
        reportText = '';
      }, 1400);
    } catch {
      submitted = false;
    } finally {
      submitting = false;
    }
  }
</script>

<AppBar title="Outages" />

<div class="px-5 pt-2 pb-24 space-y-4">
  <InspectableSection inspect={inspectOutages} title="Network map">
    <div class="card p-3">
      {#if loading}
        <Skeleton height="220px" rounded="14px" />
      {:else}
        <MalaysiaMap {outages} />
      {/if}
      <div class="px-2 pt-3 pb-1 flex items-center justify-between">
        <div class="text-[12.5px] text-ink-500">Active outages across the network</div>
        <div class="tnum text-[12.5px] font-semibold text-ink-700">{outages.length} live</div>
      </div>
    </div>
  </InspectableSection>

  <h2 class="mb-1 text-[12px] font-semibold tracking-widest text-ink-500 uppercase">
    Affected areas
  </h2>

  <InspectOverlay inspect={inspectOutages}>
    {#if loading}
      <div class="space-y-3">
        {#each [0, 1] as _ (_)}<Skeleton height="100px" rounded="20px" />{/each}
      </div>
    {:else if outages.length === 0}
      <div class="card flex items-center gap-3 p-5">
        <div
          class="grid h-10 w-10 place-items-center rounded-full bg-success-soft text-success"
        >
          <MapPin size={18} />
        </div>
        <div>
          <div class="text-[14px] font-semibold">No active outages</div>
          <div class="text-[12.5px] text-ink-500">
            Network is stable across all monitored substations.
          </div>
        </div>
      </div>
    {:else}
      {#each outages as o (o.outage_id)}
        <div class="card p-4 fade-up mb-3">
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <span class="text-[14.5px] font-semibold">{o.affected.label}</span>
                <StatusPill status={o.status} />
              </div>
              <div class="mt-0.5 text-[12.5px] text-ink-500">
                {o.cause}
                {#if o.substation}· {o.substation}{/if}
              </div>
            </div>
            <div class="text-right">
              <div class="text-[11px] text-ink-500">Affected</div>
              <div class="tnum text-[14px] font-bold">
                {o.customers_affected.toLocaleString()}
              </div>
            </div>
          </div>
          <div
            class="mt-3 grid grid-cols-2 gap-2 border-t border-ink-100 pt-3 text-[12px]"
          >
            <div>
              <div class="text-ink-500">Started</div>
              <div class="font-medium text-ink-700">{formatRelative(o.started_at)}</div>
            </div>
            <div>
              <div class="text-ink-500">ETA restoration</div>
              <div class="font-medium text-ink-700">
                {o.eta_restoration
                  ? new Date(o.eta_restoration).toLocaleTimeString('en-MY', {
                      hour: '2-digit',
                      minute: '2-digit'
                    })
                  : 'Investigating'}
              </div>
            </div>
          </div>
          <div class="mt-1 text-[11px] text-ink-300">
            Last update {formatRelative(o.last_update)}
          </div>
        </div>
      {/each}
    {/if}
  </InspectOverlay>
</div>

<button
  class="fixed bottom-[88px] right-1/2 z-20 flex h-14 items-center gap-2 rounded-full bg-Utility-orange px-5 text-white shadow-[0_10px_28px_rgba(238,122,35,0.4)] active:scale-95 transition-transform"
  style:transform="translateX(190px)"
  onclick={() => (showReport = true)}
>
  <Plus size={20} strokeWidth={2.6} />
  <span class="text-[14px] font-semibold">Report</span>
</button>

{#if showReport}
  <div
    class="sheet-backdrop"
    role="presentation"
    onclick={() => (showReport = false)}
    onkeydown={(e) => e.key === 'Escape' && (showReport = false)}
  ></div>
  <div class="sheet" role="dialog" aria-modal="true">
    <div class="mx-auto h-1.5 w-10 rounded-full bg-ink-100"></div>
    <div class="mt-3 flex items-center justify-between">
      <h3 class="text-[17px] font-semibold">Report an outage</h3>
      <button
        class="grid h-8 w-8 place-items-center rounded-full text-ink-500 active:bg-ink-100"
        aria-label="Close"
        onclick={() => (showReport = false)}
      >
        <X size={18} />
      </button>
    </div>
    {#if !submitted}
      <p class="mt-1 text-[12.5px] text-ink-500">
        Location: {session.selectedAccount?.address?.line1 ?? 'your supply address'}
      </p>
      <textarea
        bind:value={reportText}
        rows="3"
        placeholder="What's happening? (optional)"
        class="mt-3 w-full resize-none rounded-2xl bg-bg p-3 text-[14px] outline-none ring-1 ring-ink-100 focus:ring-Utility-orange"
      ></textarea>
      <button class="btn-primary mt-4" onclick={submitReport} disabled={submitting}>
        {submitting ? 'Submitting…' : 'Send report'}
      </button>
      <p class="mt-2 text-center text-[11px] text-ink-400">
        Inserts into <code class="font-mono">notifications</code> → change stream → SSE toast
      </p>
    {:else}
      <div class="py-6 text-center text-[14px] text-ink-700">
        Thanks — your report is on its way to the dispatch team.
      </div>
      {#if inspectReport}
        <button
          class="btn-secondary"
          onclick={() => {
            import('$lib/stores.svelte').then(({ mongoInspector }) =>
              mongoInspector.show(inspectReport)
            );
          }}
        >
          View Mongo insert
        </button>
      {/if}
    {/if}
  </div>
{/if}
