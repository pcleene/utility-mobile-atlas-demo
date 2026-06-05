<script lang="ts">
  import AppBar from '$lib/components/AppBar.svelte';
  import Skeleton from '$lib/components/Skeleton.svelte';
  import InspectableSection from '$lib/components/InspectableSection.svelte';
  import InspectOverlay from '$lib/components/InspectOverlay.svelte';
  import { api } from '$lib/api';
  import { session } from '$lib/stores.svelte';
  import { formatKWh, formatMYR } from '$lib/format';
  import type { DailyUsage, Insight, MongoInspect, MonthlyUsage } from '$lib/types';
  import {
    TrendingUp,
    TrendingDown,
    Lightbulb,
    Clock,
    Leaf,
    ArrowUpRight,
    ArrowDownRight
  } from '@lucide/svelte';

  type Mode = 'daily' | 'monthly';
  let mode = $state<Mode>('daily');
  let daily = $state<DailyUsage[]>([]);
  let monthly = $state<MonthlyUsage[]>([]);
  let insights = $state<Insight[]>([]);
  let inspectDaily = $state<MongoInspect | null>(null);
  let inspectMonthly = $state<MongoInspect | null>(null);
  let inspectInsights = $state<MongoInspect | null>(null);
  let loading = $state(true);

  $effect(() => {
    const acc = session.selectedAccount;
    if (!acc) return;
    void load(acc.account_no);
  });

  async function load(no: string): Promise<void> {
    loading = true;
    try {
      const [d, m, ins] = await Promise.all([
        api.usageDaily(no, 30),
        api.usageMonthly(no, 12),
        api.insights(no).catch(() => ({
          data: { insights: [] as Insight[] },
          inspect: undefined
        }))
      ]);
      daily = d.data;
      inspectDaily = d.inspect ?? null;
      monthly = m.data;
      inspectMonthly = m.inspect ?? null;
      insights = ins.data.insights;
      inspectInsights = ins.inspect ?? null;
    } catch {
      daily = [];
      monthly = [];
      insights = [];
    } finally {
      loading = false;
    }
  }

  const chartInspect = $derived(mode === 'daily' ? inspectDaily : inspectMonthly);

  // Chart geometry
  const W = 340;
  const H = 220;
  const PAD_X = 12;
  const PAD_Y_TOP = 24;
  const PAD_Y_BOT = 24;

  type Row = { label: string; total: number; peak: number; off: number };
  const rows = $derived<Row[]>(
    mode === 'daily'
      ? daily.slice(-7).map((d) => ({
          label: new Date(d.date).toLocaleDateString('en-MY', {
            weekday: 'short'
          }),
          total: d.total_kwh,
          peak: d.peak_kwh,
          off: d.offpeak_kwh
        }))
      : monthly.slice(-12).map((m) => ({
          label: new Date(`${m.month}-01`).toLocaleDateString('en-MY', {
            month: 'short'
          }),
          total: m.total_kwh,
          peak: m.peak_kwh,
          off: m.offpeak_kwh
        }))
  );
  const max = $derived(Math.max(0.1, ...rows.map((r) => r.total)));
  const slot = $derived((W - PAD_X * 2) / Math.max(1, rows.length));
  const barW = $derived(slot * 0.62);

  const periodTotal = $derived(rows.reduce((a, r) => a + r.total, 0));
  const periodCost = $derived(
    mode === 'daily'
      ? daily.slice(-7).reduce((a, d) => a + d.estimated_cost_myr, 0)
      : monthly.slice(-12).reduce((a, m) => a + m.estimated_cost_myr, 0)
  );
  const prevTotal = $derived(
    mode === 'daily'
      ? daily.slice(-14, -7).reduce((a, d) => a + d.total_kwh, 0)
      : 0
  );
  const delta = $derived(prevTotal > 0 ? (periodTotal - prevTotal) / prevTotal : 0);

  function iconFor(name: Insight['icon']) {
    switch (name) {
      case 'trend-up':
        return TrendingUp;
      case 'trend-down':
        return TrendingDown;
      case 'lightbulb':
        return Lightbulb;
      case 'clock':
        return Clock;
      case 'leaf':
        return Leaf;
    }
  }
</script>

<AppBar title="Usage" />

<div class="px-5 pt-2 pb-6 space-y-5">
  <!-- Segmented control -->
  <div class="inline-flex rounded-full bg-ink-100 p-1">
    {#each [{ id: 'daily', label: 'Daily' }, { id: 'monthly', label: 'Monthly' }] as o (o.id)}
      <button
        class="px-5 py-1.5 text-[13px] font-semibold rounded-full transition-colors"
        class:bg-surface={mode === o.id}
        class:shadow-[0_1px_3px_rgba(15,17,22,0.08)]={mode === o.id}
        class:text-ink-900={mode === o.id}
        class:text-ink-500={mode !== o.id}
        onclick={() => (mode = o.id as Mode)}
      >
        {o.label}
      </button>
    {/each}
  </div>

  <!-- Chart card -->
  <InspectOverlay inspect={chartInspect}>
  <div class="card p-5">
    {#if loading}
      <Skeleton height="200px" rounded="14px" />
    {:else if rows.length === 0}
      <div class="py-10 text-center text-[13px] text-ink-500">
        No data yet for this period.
      </div>
    {:else}
      <svg
        viewBox="0 0 {W} {H}"
        class="h-[220px] w-full"
        preserveAspectRatio="none"
        role="img"
        aria-label="Usage chart"
      >
        <!-- Gridlines -->
        {#each [0.25, 0.5, 0.75, 1] as g}
          {@const y =
            PAD_Y_TOP + (H - PAD_Y_TOP - PAD_Y_BOT) * (1 - g)}
          <line
            x1={PAD_X}
            x2={W - PAD_X}
            y1={y}
            y2={y}
            stroke="var(--color-ink-100)"
            stroke-width="1"
            stroke-dasharray="3 4"
          />
          <text
            x={PAD_X}
            y={y - 4}
            font-size="9"
            fill="var(--color-ink-300)"
          >
            {(max * g).toFixed(0)} kWh
          </text>
        {/each}

        {#each rows as r, i (i + r.label)}
          {@const cx = PAD_X + slot * i + slot / 2}
          {@const totalH =
            (r.total / max) * (H - PAD_Y_TOP - PAD_Y_BOT)}
          {@const peakH =
            (r.peak / max) * (H - PAD_Y_TOP - PAD_Y_BOT)}
          {@const offH = totalH - peakH}
          {@const baseY = H - PAD_Y_BOT}
          <g style="transition: all 300ms ease-out">
            <rect
              x={cx - barW / 2}
              y={baseY - offH}
              width={barW}
              height={Math.max(0, offH)}
              fill="var(--color-Utility-orange-soft)"
              rx="3"
            />
            <rect
              x={cx - barW / 2}
              y={baseY - totalH}
              width={barW}
              height={Math.max(0, peakH)}
              fill="var(--color-Utility-orange)"
              rx="3"
            />
            <text
              x={cx}
              y={H - 8}
              text-anchor="middle"
              font-size="10"
              fill="var(--color-ink-500)"
            >
              {r.label}
            </text>
          </g>
        {/each}
      </svg>
      <div class="flex items-center justify-end gap-3 text-[11px] text-ink-500">
        <span class="flex items-center gap-1">
          <span class="h-2 w-2 rounded-full bg-Utility-orange"></span> Peak
        </span>
        <span class="flex items-center gap-1">
          <span
            class="h-2 w-2 rounded-full bg-Utility-orange-soft ring-1 ring-Utility-orange/40"
          ></span>
          Off-peak
        </span>
      </div>
    {/if}
  </div>
  </InspectOverlay>

  <!-- Totals -->
  <div class="card grid grid-cols-3 gap-2 p-5">
    <div>
      <div class="text-[11px] font-medium tracking-wider text-ink-500 uppercase">
        Used
      </div>
      <div class="tnum text-[20px] font-bold leading-tight">
        {formatKWh(periodTotal)}
      </div>
    </div>
    <div>
      <div class="text-[11px] font-medium tracking-wider text-ink-500 uppercase">
        Estimated
      </div>
      <div class="tnum text-[20px] font-bold leading-tight">
        {formatMYR(periodCost)}
      </div>
    </div>
    <div>
      <div class="text-[11px] font-medium tracking-wider text-ink-500 uppercase">
        vs prev
      </div>
      {#if mode === 'daily' && prevTotal > 0}
        <div
          class="flex items-center gap-1 text-[18px] font-bold"
          class:text-success={delta < 0}
          class:text-warning={delta >= 0}
        >
          {#if delta >= 0}
            <ArrowUpRight size={18} />
          {:else}
            <ArrowDownRight size={18} />
          {/if}
          <span class="tnum">{Math.abs(delta * 100).toFixed(0)}%</span>
        </div>
      {:else}
        <div class="text-[14px] text-ink-300">—</div>
      {/if}
    </div>
  </div>

  <!-- Insights -->
  <InspectableSection inspect={inspectInsights} title="Insights">
    <div class="space-y-3">
      {#if loading}
        {#each [0, 1] as _ (_)}
          <Skeleton height="92px" rounded="20px" />
        {/each}
      {:else}
        {#each insights as ins, i (i + ins.title)}
          {@const Icon = iconFor(ins.icon)}
          <div class="card flex gap-3 p-4">
            <div
              class="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-Utility-orange-soft text-Utility-orange-dark"
            >
              <Icon size={18} />
            </div>
            <div class="min-w-0 flex-1">
              <div class="text-[14px] font-semibold text-ink-900">
                {ins.title}
              </div>
              <div class="mt-0.5 text-[12.5px] leading-snug text-ink-500">
                {ins.body}
              </div>
              {#if ins.estimated_savings_myr}
                <div
                  class="mt-1.5 inline-flex items-center gap-1 rounded-full bg-success-soft px-2 py-0.5 text-[11px] font-semibold text-success"
                >
                  Save ~{formatMYR(ins.estimated_savings_myr)}/mo
                </div>
              {/if}
            </div>
          </div>
        {/each}
      {/if}
    </div>
  </InspectableSection>
</div>
