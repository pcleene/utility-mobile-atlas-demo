<script lang="ts">
  import { goto } from '$app/navigation';
  import { ChevronLeft } from '@lucide/svelte';

  let {
    title = '',
    showBack = false,
    rightSlot,
    transparent = false
  }: {
    title?: string;
    showBack?: boolean;
    rightSlot?: import('svelte').Snippet;
    transparent?: boolean;
  } = $props();
</script>

<header
  class="sticky top-0 z-30 flex h-14 items-center px-4 backdrop-blur-md"
  class:bg-surface={!transparent}
  class:bg-bg={!transparent}
  style:background={transparent
    ? 'transparent'
    : 'color-mix(in oklab, var(--color-surface) 92%, transparent)'}
>
  {#if showBack}
    <button
      class="-ml-2 grid h-10 w-10 place-items-center rounded-full text-ink-700 active:bg-ink-100"
      aria-label="Back"
      onclick={() => history.back()}
    >
      <ChevronLeft size={22} />
    </button>
  {/if}
  <h1 class="flex-1 text-center text-[17px] font-semibold tracking-tight">
    {title}
  </h1>
  <div class="flex h-10 min-w-10 items-center justify-end">
    {#if rightSlot}{@render rightSlot()}{/if}
  </div>
</header>
