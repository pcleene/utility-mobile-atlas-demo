<script lang="ts">
  import { mongoInspector } from '$lib/stores.svelte';
  import { X, Copy, Check, Database, Layers, FileJson } from '@lucide/svelte';

  let tab = $state<'query' | 'docs'>('query');
  let copied = $state(false);

  const payload = $derived(mongoInspector.payload);

  // ---------- mongo-shell rendering ----------
  const ISO_DATE_RE =
    /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$/;
  const OID_RE = /^[a-f0-9]{24}$/i;

  // Detect operator-keyed objects (e.g. {$gte: ...}) so we render them inline-ish.
  function isOperatorObj(o: Record<string, unknown>): boolean {
    const keys = Object.keys(o);
    return keys.length > 0 && keys.every((k) => k.startsWith('$'));
  }

  function fmtKey(k: string): string {
    return /^[A-Za-z_$][A-Za-z0-9_$]*$/.test(k) ? k : JSON.stringify(k);
  }

  function fmtValue(v: unknown, indent: number, parentKey?: string): string {
    if (v === null) return 'null';
    if (v === undefined) return 'undefined';
    if (typeof v === 'boolean') return String(v);
    if (typeof v === 'number') return String(v);
    if (typeof v === 'string') {
      if (ISO_DATE_RE.test(v)) return `ISODate("${v}")`;
      if (parentKey === '_id' && OID_RE.test(v)) return `ObjectId("${v}")`;
      return JSON.stringify(v);
    }
    if (Array.isArray(v)) {
      if (v.length === 0) return '[]';
      const pad = ' '.repeat(indent + 2);
      const close = ' '.repeat(indent);
      const items = v.map((it) => pad + fmtValue(it, indent + 2)).join(',\n');
      return `[\n${items}\n${close}]`;
    }
    if (typeof v === 'object') {
      const obj = v as Record<string, unknown>;
      const keys = Object.keys(obj);
      if (keys.length === 0) return '{}';
      const inline =
        isOperatorObj(obj) &&
        keys.every((k) => {
          const val = obj[k];
          return (
            val === null ||
            typeof val !== 'object' ||
            (Array.isArray(val) && val.length === 0)
          );
        });
      if (inline) {
        const parts = keys
          .map((k) => `${fmtKey(k)}: ${fmtValue(obj[k], indent + 2, k)}`)
          .join(', ');
        return `{ ${parts} }`;
      }
      const pad = ' '.repeat(indent + 2);
      const close = ' '.repeat(indent);
      const lines = keys
        .map((k) => `${pad}${fmtKey(k)}: ${fmtValue(obj[k], indent + 2, k)}`)
        .join(',\n');
      return `{\n${lines}\n${close}}`;
    }
    return String(v);
  }

  function fmtArg(v: unknown): string {
    return fmtValue(v, 0);
  }

  function mongoShell(p: NonNullable<typeof payload>): string {
    const coll = `db.${p.collection}`;
    const op = p.operation.toLowerCase();
    const hint = p.index ? `\n  .hint(${JSON.stringify(p.index)})` : '';

    if (op === 'aggregate' && p.pipeline?.length) {
      return `${coll}.aggregate(${fmtArg(p.pipeline)})`;
    }
    if (op === 'watch') {
      return `${coll}.watch(${p.pipeline?.length ? fmtArg(p.pipeline) : ''})`;
    }
    if (op === 'findone') {
      return `${coll}.findOne(${fmtArg(p.filter ?? {})})`;
    }
    if (op === 'find') {
      let s = `${coll}.find(${fmtArg(p.filter ?? {})})`;
      if (p.sort) s += `\n  .sort(${fmtArg(p.sort)})`;
      if (p.limit != null) s += `\n  .limit(${p.limit})`;
      s += hint;
      return s;
    }
    if (op === 'insertone') {
      return `${coll}.insertOne(${fmtArg(p.sample_documents?.[0] ?? p.filter ?? {})})`;
    }
    if (op === 'updateone' || op === 'updatemany') {
      return `${coll}.${op === 'updateone' ? 'updateOne' : 'updateMany'}(${fmtArg(p.filter ?? {})}, ${fmtArg(p.sample_documents?.[0] ?? {})})`;
    }
    if (op === 'countdocuments') {
      return `${coll}.countDocuments(${fmtArg(p.filter ?? {})})`;
    }
    // Generic fallback
    if (p.pipeline?.length) return `${coll}.aggregate(${fmtArg(p.pipeline)})`;
    return `${coll}.${p.operation}(${fmtArg(p.filter ?? {})})`;
  }

  function shellHighlight(src: string): string {
    // Escape HTML
    let s = src
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    // Strings (not yet wrapped in spans)
    s = s.replace(/"([^"\\]|\\.)*"/g, (m) => `<span class="tk-str">${m}</span>`);
    // Numbers
    s = s.replace(
      /(^|[\s,\[\(:])(-?\d+(?:\.\d+)?)/g,
      (_m, p1, p2) => `${p1}<span class="tk-num">${p2}</span>`,
    );
    // Booleans / null
    s = s.replace(/\b(true|false|null|undefined)\b/g, '<span class="tk-bool">$1</span>');
    // Helpers — ISODate/ObjectId
    s = s.replace(
      /\b(ISODate|ObjectId)\b/g,
      '<span class="tk-helper">$1</span>',
    );
    // Mongo operators ($gte, $vectorSearch, etc.) — they appear as keys before ":".
    s = s.replace(/(\$[A-Za-z][A-Za-z0-9]*)(?=\s*:)/g, '<span class="tk-op">$1</span>');
    // db.<coll>.<method>(
    s = s.replace(
      /\b(db)\.([A-Za-z0-9_]+)\.([A-Za-z]+)/g,
      '<span class="tk-db">$1</span>.<span class="tk-coll">$2</span>.<span class="tk-fn">$3</span>',
    );
    // .sort/.limit/.hint chained calls
    s = s.replace(
      /\.(sort|limit|hint|skip|project)\(/g,
      '.<span class="tk-fn">$1</span>(',
    );
    return s;
  }

  async function copy(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      copied = true;
      setTimeout(() => (copied = false), 1600);
    } catch {
      /* ignore */
    }
  }

  function featureColor(f: string): string {
    const k = f.toLowerCase();
    if (k.includes('search')) return 'bg-emerald-500/15 text-emerald-700';
    if (k.includes('vector')) return 'bg-violet-500/15 text-violet-700';
    if (k.includes('geo')) return 'bg-sky-500/15 text-sky-700';
    if (k.includes('time')) return 'bg-amber-500/15 text-amber-800';
    if (k.includes('change')) return 'bg-rose-500/15 text-rose-700';
    if (k.includes('shard')) return 'bg-indigo-500/15 text-indigo-700';
    return 'bg-white/10 text-white/80';
  }
</script>

{#if mongoInspector.open && payload}
  <div
    class="inspect-backdrop"
    role="presentation"
    onclick={() => mongoInspector.close()}
    onkeydown={(e) => e.key === 'Escape' && mongoInspector.close()}
  ></div>

  <div
    class="inspect-panel"
    role="dialog"
    aria-modal="true"
    aria-label="MongoDB query inspector"
  >
    <!-- Header -->
    <div class="inspect-header">
      <div class="flex min-w-0 flex-1 items-start gap-3">
        <div
          class="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-[#13AA52]/20 text-[#47D686]"
        >
          <Database size={22} />
        </div>
        <div class="min-w-0 flex-1">
          <div class="text-[11px] font-bold tracking-[0.14em] text-[#47D686] uppercase">
            MongoDB Atlas
          </div>
          <h2 class="truncate text-[17px] font-semibold text-white">
            {payload.title}
          </h2>
          <div class="mt-0.5 flex flex-wrap items-center gap-2 text-[11px] text-white/50">
            <span class="font-mono">{payload.collection}</span>
            <span>·</span>
            <span class="rounded bg-white/10 px-1.5 py-0.5 font-mono uppercase">
              {payload.operation}
            </span>
            {#if payload.engine}
              <span>·</span>
              <span>{payload.engine}</span>
            {/if}
          </div>
        </div>
      </div>
      <button
        class="grid h-9 w-9 shrink-0 place-items-center rounded-full text-white/60 hover:bg-white/10 hover:text-white"
        aria-label="Close inspector"
        onclick={() => mongoInspector.close()}
      >
        <X size={18} />
      </button>
    </div>

    <!-- Feature chips -->
    <div class="flex flex-wrap gap-1.5 px-4 pb-3">
      {#each payload.features as f (f)}
        <span class="rounded-full px-2.5 py-1 text-[10px] font-semibold tracking-wide uppercase {featureColor(f)}">
          {f}
        </span>
      {/each}
    </div>

    <!-- Tabs -->
    <div class="inspect-tabs">
      <button
        class="inspect-tab"
        class:inspect-tab-active={tab === 'query'}
        onclick={() => (tab = 'query')}
      >
        <Layers size={14} />
        {payload.pipeline?.length ? 'Pipeline' : 'Query'}
      </button>
      <button
        class="inspect-tab"
        class:inspect-tab-active={tab === 'docs'}
        onclick={() => (tab = 'docs')}
      >
        <FileJson size={14} />
        Documents ({payload.sample_documents.length})
      </button>
    </div>

    <!-- Body -->
    <div class="inspect-body">
      {#if tab === 'query'}
        <div class="inspect-meta">
          <div class="inspect-meta-row">
            <span class="inspect-meta-key">endpoint</span>
            <code class="inspect-meta-val">{payload.endpoint}</code>
          </div>
          {#if payload.indexes?.length}
            <div class="inspect-meta-row">
              <span class="inspect-meta-key">index</span>
              <code class="inspect-meta-val">{payload.indexes.join(', ')}</code>
            </div>
          {/if}
          {#if payload.note}
            <p class="inspect-note">{payload.note}</p>
          {/if}
        </div>
        <div class="inspect-code-wrap">
          <button
            class="inspect-copy"
            onclick={() => copy(mongoShell(payload))}
            aria-label="Copy query"
          >
            {#if copied}
              <Check size={14} /> Copied
            {:else}
              <Copy size={14} /> Copy
            {/if}
          </button>
          <pre class="inspect-code"><code>{@html shellHighlight(mongoShell(payload))}</code></pre>
        </div>
      {:else}
        {#if payload.sample_documents.length === 0}
          <div class="inspect-empty">
            No sample documents — this section is client-side or streams live events.
          </div>
        {:else}
          {#each payload.sample_documents as doc, i (i)}
            <div class="inspect-doc">
              <div class="inspect-doc-label">Document {i + 1}</div>
              <pre class="inspect-code inspect-code-doc"><code>{@html shellHighlight(fmtArg(doc))}</code></pre>
            </div>
          {/each}
        {/if}
      {/if}
    </div>

    <div class="inspect-footer">
      <span class="text-[10px] text-white/35 font-mono">UtilityApp · Atlas inspector</span>
      <button
        class="text-[12px] font-semibold text-[#47D686] hover:text-[#7AE8A8]"
        onclick={() => mongoInspector.close()}
      >
        Done
      </button>
    </div>
  </div>
{/if}

<style>
  .inspect-backdrop {
    position: fixed;
    inset: 0;
    z-index: 80;
    background: rgb(8 10 14 / 55%);
    backdrop-filter: blur(6px);
    animation: inspect-fade 200ms ease-out;
  }
  .inspect-panel {
    position: fixed;
    z-index: 81;
    left: 50%;
    bottom: 0;
    transform: translateX(-50%);
    width: min(100%, 480px);
    max-height: min(88dvh, 720px);
    display: flex;
    flex-direction: column;
    background: linear-gradient(180deg, #141820 0%, #0e1116 100%);
    border-top-left-radius: 24px;
    border-top-right-radius: 24px;
    box-shadow:
      0 -12px 48px rgb(0 0 0 / 35%),
      0 0 0 1px rgb(255 255 255 / 6%);
    animation: inspect-slide 280ms cubic-bezier(0.18, 0.9, 0.32, 1);
    color: white;
  }
  .inspect-header {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 1.1rem 1rem 0.5rem;
  }
  .inspect-tabs {
    display: flex;
    gap: 0.35rem;
    padding: 0 1rem 0.75rem;
    border-bottom: 1px solid rgb(255 255 255 / 8%);
  }
  .inspect-tab {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.45rem 0.85rem;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    color: rgb(255 255 255 / 45%);
    transition: all 120ms ease;
  }
  .inspect-tab-active {
    background: rgb(19 170 82 / 18%);
    color: #7ae8a8;
  }
  .inspect-body {
    flex: 1;
    overflow-y: auto;
    padding: 0 1rem 1rem;
    min-height: 0;
  }
  .inspect-meta {
    margin-bottom: 0.75rem;
    padding: 0.75rem;
    border-radius: 12px;
    background: rgb(255 255 255 / 4%);
    border: 1px solid rgb(255 255 255 / 6%);
  }
  .inspect-meta-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem 0.75rem;
    font-size: 11px;
    margin-bottom: 0.35rem;
  }
  .inspect-meta-key {
    color: rgb(255 255 255 / 40%);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
  }
  .inspect-meta-val {
    font-family: ui-monospace, monospace;
    color: #fbbf24;
    word-break: break-all;
  }
  .inspect-note {
    margin-top: 0.5rem;
    font-size: 12px;
    line-height: 1.45;
    color: rgb(255 255 255 / 55%);
  }
  .inspect-code-wrap {
    position: relative;
  }
  .inspect-copy {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    z-index: 2;
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.3rem 0.55rem;
    border-radius: 8px;
    font-size: 11px;
    font-weight: 600;
    color: rgb(255 255 255 / 70%);
    background: rgb(255 255 255 / 8%);
    border: 1px solid rgb(255 255 255 / 10%);
  }
  .inspect-code {
    margin: 0;
    padding: 1rem 0.85rem;
    border-radius: 14px;
    background: #06080b;
    border: 1px solid rgb(255 255 255 / 8%);
    font-family: ui-monospace, 'SF Mono', Menlo, monospace;
    font-size: 11.5px;
    line-height: 1.55;
    color: #c9d1d9;
    overflow-x: auto;
    white-space: pre;
  }
  .inspect-code :global(.tk-str) { color: #a5d6a7; }
  .inspect-code :global(.tk-num) { color: #ffb86c; }
  .inspect-code :global(.tk-bool) { color: #ff79c6; }
  .inspect-code :global(.tk-op) { color: #82aaff; font-weight: 600; }
  .inspect-code :global(.tk-helper) { color: #f7c948; }
  .inspect-code :global(.tk-db) { color: #6272a4; }
  .inspect-code :global(.tk-coll) { color: #47d686; font-weight: 600; }
  .inspect-code :global(.tk-fn) { color: #d2a8ff; }
  .inspect-code-doc {
    margin-top: 0.35rem;
    max-height: 220px;
    overflow: auto;
  }
  .inspect-doc {
    margin-bottom: 0.75rem;
  }
  .inspect-doc-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: rgb(255 255 255 / 35%);
  }
  .inspect-empty {
    padding: 2rem 1rem;
    text-align: center;
    font-size: 13px;
    color: rgb(255 255 255 / 45%);
  }
  .inspect-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1rem calc(0.85rem + var(--safe-bottom));
    border-top: 1px solid rgb(255 255 255 / 8%);
  }
  @keyframes inspect-fade {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
  @keyframes inspect-slide {
    from {
      transform: translateX(-50%) translateY(100%);
    }
    to {
      transform: translateX(-50%) translateY(0);
    }
  }
</style>
