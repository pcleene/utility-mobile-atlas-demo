<script lang="ts">
  import '../app.css';
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  import { session } from '$lib/stores.svelte';
  import { connectNotificationStream } from '$lib/sse';
  import BottomTabBar from '$lib/components/BottomTabBar.svelte';
  import Toasts from '$lib/components/Toasts.svelte';
  import MongoInspectSheet from '$lib/components/MongoInspectSheet.svelte';

  let { children } = $props();
  let bootError = $state<string | null>(null);

  onMount(async () => {
    try {
      const { data } = await api.me();
      session.setCustomer(data);
      connectNotificationStream();
    } catch (e) {
      bootError = (e as Error).message;
      session.hydrated = true;
    }
  });
</script>

<div class="app-shell flex min-h-dvh flex-col">
  <main class="relative flex-1 pb-2">
    {@render children?.()}
    {#if bootError}
      <div
        class="mx-4 mt-4 rounded-xl bg-danger-soft px-4 py-3 text-sm text-danger ring-1 ring-danger/10"
      >
        Backend unreachable — {bootError}. Make sure the FastAPI server is
        running.
      </div>
    {/if}
  </main>
  <BottomTabBar />
  <Toasts />
  <MongoInspectSheet />
</div>
