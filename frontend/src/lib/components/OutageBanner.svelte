<script lang="ts">
  import type { Outage } from '$lib/types';
  import StatusPill from './StatusPill.svelte';
  import { CheckCircle2, TriangleAlert, ArrowRight } from '@lucide/svelte';
  import { formatRelative } from '$lib/format';
  import { goto } from '$app/navigation';

  let { outages }: { outages: Outage[] } = $props();
  const first = $derived(outages[0] ?? null);
</script>

{#if first}
  <button
    class="card-press card flex w-full items-center gap-3 border-l-4 border-l-warning p-4 text-left"
    onclick={() => goto('/outages')}
  >
    <div
      class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-warning-soft text-warning"
    >
      <TriangleAlert size={20} />
    </div>
    <div class="min-w-0 flex-1">
      <div class="flex items-center gap-2">
        <span class="text-[13px] font-semibold text-ink-900"
          >Outage in your area</span
        >
        <StatusPill status={first.status} />
      </div>
      <div class="mt-0.5 line-clamp-1 text-[12.5px] text-ink-500">
        {first.cause}
      </div>
      <div class="mt-0.5 text-[11.5px] text-ink-500">
        {first.affected.label} · updated {formatRelative(first.last_update)}
      </div>
    </div>
    <ArrowRight size={18} class="shrink-0 text-ink-300" />
  </button>
{:else}
  <div class="card flex items-center gap-3 p-4">
    <div
      class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-success-soft text-success"
    >
      <CheckCircle2 size={20} />
    </div>
    <div class="flex-1">
      <div class="text-[13px] font-semibold text-ink-900">
        No outages in your area
      </div>
      <div class="text-[12px] text-ink-500">
        Sambungan elektrik anda stabil.
      </div>
    </div>
  </div>
{/if}
