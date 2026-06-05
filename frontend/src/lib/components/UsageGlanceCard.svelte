<script lang="ts">
  import type { DailyUsage } from '$lib/types';
  import UsageMiniChart from './UsageMiniChart.svelte';
  import { formatKWh, formatMYR } from '$lib/format';
  import { goto } from '$app/navigation';
  import { ArrowRight, Activity } from '@lucide/svelte';

  let { daily }: { daily: DailyUsage[] } = $props();

  const last7 = $derived(daily.slice(-7));
  const totalKwh = $derived(last7.reduce((a, d) => a + d.total_kwh, 0));
  const totalCost = $derived(last7.reduce((a, d) => a + d.estimated_cost_myr, 0));
</script>

<div class="card p-5">
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-2 text-[13px] font-semibold text-ink-700">
      <Activity size={15} class="text-Utility-orange" /> Last 7 days
    </div>
    <button
      class="flex items-center gap-1 text-[12.5px] font-medium text-Utility-orange-dark"
      onclick={() => goto('/usage')}
    >
      Details <ArrowRight size={14} />
    </button>
  </div>

  <div class="mt-3">
    <UsageMiniChart {daily} />
  </div>

  <div class="mt-3 flex items-end justify-between border-t border-ink-100 pt-3">
    <div>
      <div class="text-[11.5px] text-ink-500">Total used</div>
      <div class="tnum text-[18px] font-bold leading-tight">{formatKWh(totalKwh)}</div>
    </div>
    <div class="text-right">
      <div class="text-[11.5px] text-ink-500">Estimated cost</div>
      <div class="tnum text-[18px] font-bold leading-tight">{formatMYR(totalCost)}</div>
    </div>
    <div class="flex items-center gap-1 text-[11px] text-ink-500">
      <span class="h-2 w-2 rounded-full bg-Utility-orange"></span> Peak
      <span class="ml-2 h-2 w-2 rounded-full bg-Utility-orange-soft ring-1 ring-Utility-orange/40"></span>
      Off-peak
    </div>
  </div>
</div>
