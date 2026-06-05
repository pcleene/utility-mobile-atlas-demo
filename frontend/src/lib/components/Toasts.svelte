<script lang="ts">
  import { toasts } from '$lib/stores.svelte';
  import { X, BellRing } from '@lucide/svelte';
</script>

<div
  class="pointer-events-none fixed top-3 right-3 z-50 flex max-w-[88vw] flex-col gap-2"
  style:max-width="320px"
>
  {#each toasts.items as t (t.id)}
    <div
      class="toast pointer-events-auto flex gap-3 rounded-2xl bg-surface p-3 pr-2 shadow-[0_8px_24px_rgba(15,17,22,0.12)] ring-1 ring-ink-100"
    >
      <div
        class="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-Utility-orange-soft text-Utility-orange-dark"
      >
        <BellRing size={18} />
      </div>
      <div class="min-w-0 flex-1 pt-0.5">
        <div class="truncate text-[13px] font-semibold text-ink-900">
          {t.title}
        </div>
        <div class="line-clamp-2 text-[12px] leading-snug text-ink-500">
          {t.body}
        </div>
      </div>
      <button
        class="grid h-8 w-8 shrink-0 place-items-center rounded-full text-ink-500 active:bg-ink-100"
        aria-label="Dismiss"
        onclick={() => toasts.dismiss(t.id)}
      >
        <X size={16} />
      </button>
    </div>
  {/each}
</div>
