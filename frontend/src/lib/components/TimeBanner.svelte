<script lang="ts">
  import { isPeakNow } from '$lib/format';
  import { Clock, Moon } from '@lucide/svelte';

  const now = new Date();
  const peak = isPeakNow(now);
</script>

<div
  class="flex items-center gap-3 rounded-2xl px-4 py-3"
  class:bg-warning-soft={peak}
  class:bg-Utility-blue-soft={!peak}
>
  <div
    class="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-white/70"
  >
    {#if peak}
      <Clock size={18} class="text-warning" />
    {:else}
      <Moon size={18} class="text-Utility-blue" />
    {/if}
  </div>
  <div class="min-w-0 flex-1">
    <div class="text-[12.5px] font-semibold text-ink-900">
      {peak ? 'Peak hours now' : 'Off-peak hours'}
    </div>
    <div class="text-[11.5px] leading-snug text-ink-500">
      {peak
        ? 'Heavy loads after 10 pm cost ~14% less.'
        : 'Right now is a great time for laundry, dishwashing, and EV charging.'}
    </div>
  </div>
</div>
