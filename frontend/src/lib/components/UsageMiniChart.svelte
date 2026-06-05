<script lang="ts">
  import type { DailyUsage } from '$lib/types';

  let { daily }: { daily: DailyUsage[] } = $props();

  const last7 = $derived(daily.slice(-7));
  const max = $derived(Math.max(0.1, ...last7.map((d) => d.total_kwh)));

  const W = 280;
  const H = 88;
  const PAD = 4;
  const COUNT = 7;
  const slot = (W - PAD * 2) / COUNT;
  const barW = slot * 0.62;
</script>

<svg
  viewBox="0 0 {W} {H}"
  class="h-[88px] w-full"
  preserveAspectRatio="none"
  role="img"
  aria-label="7-day energy usage"
>
  {#each last7 as d, i (d.date)}
    {@const cx = PAD + slot * i + slot / 2}
    {@const totalH = (d.total_kwh / max) * (H - 18)}
    {@const peakH = (d.peak_kwh / max) * (H - 18)}
    {@const offH = totalH - peakH}
    <g>
      <rect
        x={cx - barW / 2}
        y={H - 14 - offH}
        width={barW}
        height={Math.max(0, offH)}
        fill="var(--color-Utility-orange-soft)"
        rx="3"
      />
      <rect
        x={cx - barW / 2}
        y={H - 14 - totalH}
        width={barW}
        height={Math.max(0, peakH)}
        fill="var(--color-Utility-orange)"
        rx="3"
      />
      <text
        x={cx}
        y={H - 2}
        text-anchor="middle"
        font-size="9"
        fill="var(--color-ink-500)"
      >
        {new Date(d.date).toLocaleDateString('en-MY', { weekday: 'narrow' })}
      </text>
    </g>
  {/each}
</svg>
