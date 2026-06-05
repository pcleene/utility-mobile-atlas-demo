<script lang="ts">
  import type { MongoInspect } from '$lib/types';
  import InspectButton from './InspectButton.svelte';

  let {
    inspect,
    class: cls = '',
    align = 'right',
    children
  }: {
    inspect?: MongoInspect | null;
    class?: string;
    align?: 'left' | 'right';
    children?: import('svelte').Snippet;
  } = $props();
</script>

<div class="inspect-wrap {cls}">
  {#if inspect}
    <div class="inspect-strip" class:left={align === 'left'}>
      <InspectButton {inspect} />
    </div>
  {/if}
  {@render children?.()}
</div>

<style>
  .inspect-wrap {
    position: relative;
  }
  .inspect-strip {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 0.5rem;
  }
  .inspect-strip.left {
    justify-content: flex-start;
  }
</style>
