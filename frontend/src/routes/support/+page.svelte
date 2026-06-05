<script lang="ts">
  import AppBar from '$lib/components/AppBar.svelte';
  import Skeleton from '$lib/components/Skeleton.svelte';
  import InspectableSection from '$lib/components/InspectableSection.svelte';
  import { api } from '$lib/api';
  import type { MongoInspect, SupportHit } from '$lib/types';
  import { Search, Headphones, Sparkles } from '@lucide/svelte';

  let query = $state('');
  let lang = $state<'EN' | 'BM' | 'ZH'>('EN');
  let hits = $state<SupportHit[]>([]);
  let engine = $state<string>('');
  let inspectSearch = $state<MongoInspect | null>(null);
  let loading = $state(false);

  let debounceId: ReturnType<typeof setTimeout> | null = null;

  $effect(() => {
    const q = query.trim();
    if (debounceId) clearTimeout(debounceId);
    if (q.length === 0) {
      hits = [];
      engine = '';
      inspectSearch = null;
      loading = false;
      return;
    }
    debounceId = setTimeout(() => void run(q), 300);
  });

  async function run(q: string) {
    loading = true;
    try {
      const res = await api.supportSearch(q, lang, 10);
      hits = res.data.hits;
      engine = res.data.engine;
      inspectSearch = res.inspect ?? null;
    } catch {
      hits = [];
      engine = 'error';
      inspectSearch = null;
    } finally {
      loading = false;
    }
  }

  const topics = ['Billing', 'Tariff', 'Outage', 'Smart Meter'];

  const phrasings = {
    EN: 'Ask anything — bills, tariffs, outages…',
    BM: 'Tanya apa-apa — bil, tarif, gangguan…',
    ZH: '随便问 — 账单、电价、停电…'
  } as const;
</script>

<AppBar title="Support" />

<div class="px-5 pt-2 pb-6 space-y-4">
  <div
    class="card flex items-center gap-2 px-3 py-2 ring-1 ring-ink-100 focus-within:ring-Utility-orange/60"
  >
    <Search size={18} class="text-ink-500" />
    <input
      type="search"
      bind:value={query}
      placeholder={phrasings[lang]}
      class="flex-1 bg-transparent py-2 text-[14px] outline-none placeholder:text-ink-300"
    />
    <select
      bind:value={lang}
      class="rounded-md bg-bg px-2 py-1 text-[12px] font-semibold outline-none"
    >
      <option value="EN">EN</option>
      <option value="BM">BM</option>
      <option value="ZH">ZH</option>
    </select>
  </div>

  <div class="flex flex-wrap gap-2">
    {#each topics as t (t)}
      <button
        class="rounded-full bg-Utility-orange-soft px-3 py-1.5 text-[12.5px] font-semibold text-Utility-orange-dark active:scale-95 transition-transform"
        onclick={() => (query = t)}
      >
        {t}
      </button>
    {/each}
  </div>

  {#if query.trim().length === 0}
    <div class="card p-6 text-center">
      <div
        class="mx-auto grid h-12 w-12 place-items-center rounded-full bg-Utility-blue-soft text-Utility-blue"
      >
        <Sparkles size={20} />
      </div>
      <h3 class="mt-3 text-[15px] font-semibold">Hybrid AI search</h3>
      <p class="mt-1 text-[12.5px] text-ink-500">
        Lexical (BM25) + Atlas Vector Search (Voyage AI). Tap <strong>↔ Mongo</strong> on
        results to inspect the aggregation pipeline.
      </p>
    </div>
  {:else if loading}
    <div class="space-y-3">
      {#each [0, 1, 2] as _ (_)}<Skeleton height="80px" rounded="20px" />{/each}
    </div>
  {:else if hits.length === 0}
    <div class="card p-6 text-center text-[13px] text-ink-500">
      No matches found. Try a different phrase.
    </div>
  {:else}
    <InspectableSection
      inspect={inspectSearch}
      title="Search results · {engine}"
    >
      <div class="space-y-3">
          {#each hits as h (h.ticket_id)}
            <div class="card p-4 fade-up">
              <div class="flex items-center gap-2">
                <span class="pill pill-blue">{h.category}</span>
                <span class="pill pill-muted">{h.lang}</span>
                <span class="ml-auto tnum text-[10.5px] text-ink-300">
                  {h.score.toFixed(3)} · {h.matched_via}
                </span>
              </div>
              <h3 class="mt-2 text-[14.5px] font-semibold leading-snug">{h.title}</h3>
              <p class="mt-0.5 line-clamp-2 text-[12.5px] text-ink-500">{h.summary}</p>
              {#if h.resolution_steps.length > 0}
                <ol class="mt-2 list-decimal space-y-0.5 pl-4 text-[12px] text-ink-700">
                  {#each h.resolution_steps.slice(0, 2) as s, i (i)}
                    <li>{s}</li>
                  {/each}
                </ol>
              {/if}
            </div>
          {/each}
        </div>
    </InspectableSection>
  {/if}

  <button class="card-press card flex w-full items-center gap-3 p-4 text-left">
    <div
      class="grid h-10 w-10 place-items-center rounded-full bg-Utility-orange-soft text-Utility-orange-dark"
    >
      <Headphones size={18} />
    </div>
    <div class="flex-1">
      <div class="text-[14px] font-semibold">Chat with Careline</div>
      <div class="text-[12px] text-ink-500">15-300-88 · 24/7</div>
    </div>
  </button>
</div>
