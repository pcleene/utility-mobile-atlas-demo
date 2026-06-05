<script lang="ts">
  import { onMount } from 'svelte';
  import AppBar from '$lib/components/AppBar.svelte';
  import InspectableSection from '$lib/components/InspectableSection.svelte';
  import { api } from '$lib/api';
  import { session } from '$lib/stores.svelte';
  import { STATIC_INSPECT } from '$lib/staticInspect';
  import type { MongoInspect } from '$lib/types';
  import {
    Wallet,
    Bell,
    Languages,
    Moon,
    ShieldCheck,
    LogOut,
    Building2,
    ChevronRight
  } from '@lucide/svelte';

  let inspectProfile = $state<MongoInspect | null>(null);

  onMount(async () => {
    try {
      const res = await api.me();
      inspectProfile = res.inspect ?? null;
    } catch {
      inspectProfile = STATIC_INSPECT.profile;
    }
  });

  const items = [
    { icon: Building2, label: 'Linked accounts', sub: 'Manage your supply points' },
    { icon: Wallet, label: 'Payment methods', sub: 'JomPAY, FPX, InstantTransfer, cards' },
    { icon: Bell, label: 'Notifications', sub: 'Outages, bills, promos' },
    { icon: Languages, label: 'Language', sub: 'BM · EN · 中文' },
    { icon: Moon, label: 'Dark mode', sub: 'System default' },
    { icon: ShieldCheck, label: 'MyDigital ID', sub: 'Biometric & 2FA' }
  ];
</script>

<AppBar title="More" />

<div class="px-5 pt-2 pb-6 space-y-4">
  <InspectableSection inspect={inspectProfile ?? STATIC_INSPECT.profile} title="Profile">
    <div class="card flex items-center gap-3 p-4">
      <div
        class="grid h-14 w-14 place-items-center rounded-full text-[20px] font-bold text-white"
        style:background={session.customer?.avatar_color ?? '#EE7A23'}
      >
        {(session.customer?.name ?? 'A').slice(0, 1)}
      </div>
      <div class="min-w-0 flex-1">
        <div class="truncate text-[16px] font-semibold">
          {session.customer?.name ?? '—'}
        </div>
        <div class="text-[12.5px] text-ink-500">{session.customer?.email ?? '—'}</div>
        <div class="text-[12px] text-ink-500">
          IC {session.customer?.ic_masked ?? '—'}
        </div>
      </div>
    </div>
  </InspectableSection>

  <InspectableSection inspect={STATIC_INSPECT.sse} title="Live notifications">
    <div class="card px-4 py-3 text-[12.5px] text-ink-500">
      Change streams on <code class="font-mono text-ink-700">bills</code>,
      <code class="font-mono text-ink-700">outages</code>, and
      <code class="font-mono text-ink-700">notifications</code> push SSE toasts while you
      browse.
    </div>
  </InspectableSection>

  <div class="card divide-y divide-ink-100 p-0">
    {#each items as it (it.label)}
      <button class="flex w-full items-center gap-3 p-4 text-left active:bg-ink-100/40">
        <div
          class="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-Utility-blue-soft text-Utility-blue"
        >
          <it.icon size={16} />
        </div>
        <div class="min-w-0 flex-1">
          <div class="text-[14px] font-semibold">{it.label}</div>
          <div class="text-[12px] text-ink-500">{it.sub}</div>
        </div>
        <ChevronRight size={18} class="text-ink-300" />
      </button>
    {/each}
  </div>

  <button
    class="card flex w-full items-center justify-center gap-2 p-4 text-[14px] font-semibold text-danger active:bg-danger-soft/40"
  >
    <LogOut size={16} /> Log out
  </button>

  <div class="text-center text-[11px] text-ink-300">
    UtilityApp clone · v1.0 · MongoDB Atlas reference
  </div>
</div>
