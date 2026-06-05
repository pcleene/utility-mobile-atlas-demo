<script lang="ts">
  import { Clock, Leaf, MessageCircleWarning, MapPin } from '@lucide/svelte';

  const actions = [
    { label: 'Apply ToU', sub: 'Time-of-Use', Icon: Clock, tint: 'bg-Utility-blue-soft text-Utility-blue' },
    { label: 'Green Energy', sub: 'myGreen+', Icon: Leaf, tint: 'bg-success-soft text-success' },
    { label: 'Report Outage', sub: 'Quick form', Icon: MessageCircleWarning, tint: 'bg-warning-soft text-warning' },
    { label: 'Service Centre', sub: 'Find branch', Icon: MapPin, tint: 'bg-Utility-orange-soft text-Utility-orange-dark' }
  ];
</script>

<div class="grid grid-cols-4 gap-3">
  {#each actions as a (a.label)}
    <button
      class="card-press flex flex-col items-center gap-1.5 rounded-2xl bg-surface p-3 shadow-[0_1px_2px_rgba(15,17,22,0.04),0_4px_12px_rgba(15,17,22,0.04)]"
    >
      <span class="grid h-10 w-10 place-items-center rounded-2xl {a.tint}">
        <a.Icon size={18} strokeWidth={2.2} />
      </span>
      <span class="text-center text-[11.5px] leading-tight font-semibold text-ink-700">
        {a.label}
      </span>
    </button>
  {/each}
</div>
