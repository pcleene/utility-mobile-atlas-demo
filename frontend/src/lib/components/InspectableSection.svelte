<script lang="ts">
  import type { MongoInspect } from '$lib/types';
  import InspectButton from './InspectButton.svelte';

  let {
    inspect,
    title,
    class: cls = '',
    children
  }: {
    inspect?: MongoInspect | null;
    title?: string;
    class?: string;
    children?: import('svelte').Snippet;
  } = $props();
</script>

<section class="inspectable-section {cls}">
  {#if title || inspect}
    <div class="inspectable-section-head">
      {#if title}
        <h2 class="inspectable-section-title">{title}</h2>
      {:else}
        <span></span>
      {/if}
      {#if inspect}
        <InspectButton {inspect} />
      {/if}
    </div>
  {/if}
  <div class="inspectable-section-body">
    {@render children?.()}
  </div>
</section>

<style>
  .inspectable-section {
    position: relative;
  }
  .inspectable-section-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
  }
  .inspectable-section-title {
    font-size: 14px;
    font-weight: 600;
    letter-spacing: -0.01em;
    color: var(--color-ink-700);
  }
  .inspectable-section-body {
    position: relative;
  }
</style>
