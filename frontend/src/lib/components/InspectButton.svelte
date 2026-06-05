<script lang="ts">
  import type { MongoInspect } from '$lib/types';
  import { mongoInspector } from '$lib/stores.svelte';

  let {
    inspect,
    label = 'Inspect query',
    class: cls = ''
  }: {
    inspect: MongoInspect | null | undefined;
    label?: string;
    class?: string;
  } = $props();
</script>

{#if inspect}
  <button
    type="button"
    class="inspect-trigger {cls}"
    aria-label={label}
    title={label}
    onclick={(e) => {
      e.stopPropagation();
      mongoInspector.show(inspect);
    }}
  >
    <span class="inspect-trigger-icon" aria-hidden="true">↔</span>
    <span class="inspect-trigger-label">Mongo</span>
  </button>
{/if}

<style>
  .inspect-trigger {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.28rem 0.55rem 0.28rem 0.45rem;
    border-radius: 999px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #00684a;
    background: linear-gradient(135deg, #e8fff4 0%, #d4f7e8 100%);
    border: 1px solid rgb(0 104 74 / 18%);
    box-shadow:
      0 1px 2px rgb(15 17 22 / 4%),
      inset 0 1px 0 rgb(255 255 255 / 70%);
    transition:
      transform 120ms ease,
      box-shadow 120ms ease,
      background 120ms ease;
    cursor: pointer;
    z-index: 20;
  }
  .inspect-trigger:hover {
    background: linear-gradient(135deg, #d4f7e8 0%, #b8efd8 100%);
    box-shadow: 0 2px 8px rgb(0 104 74 / 14%);
  }
  .inspect-trigger:active {
    transform: scale(0.96);
  }
  .inspect-trigger-icon {
    font-size: 12px;
    line-height: 1;
    font-weight: 800;
    color: #13aa52;
  }
  .inspect-trigger-label {
    font-family: ui-monospace, 'SF Mono', Menlo, monospace;
  }
</style>
