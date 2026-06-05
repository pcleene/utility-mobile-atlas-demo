<script lang="ts">
  import { page } from '$app/stores';
  import { House, Receipt, Zap, TriangleAlert, CircleEllipsis } from '@lucide/svelte';

  const tabs = [
    { href: '/', label: 'Home', icon: House },
    { href: '/bills', label: 'Bills', icon: Receipt },
    { href: '/usage', label: 'Usage', icon: Zap },
    { href: '/outages', label: 'Outages', icon: TriangleAlert },
    { href: '/more', label: 'More', icon: CircleEllipsis }
  ];

  const activeIdx = $derived(
    tabs.findIndex((t) => {
      const p = $page.url.pathname;
      if (t.href === '/') return p === '/';
      return p === t.href || p.startsWith(t.href + '/');
    })
  );
</script>

<nav
  class="sticky bottom-0 z-30 grid grid-cols-5 border-t border-ink-100 bg-surface/95 backdrop-blur-md"
  style:padding-bottom="var(--safe-bottom)"
  style:box-shadow="var(--shadow-tab)"
>
  {#each tabs as tab, i (tab.href)}
    {@const Icon = tab.icon}
    <a
      href={tab.href}
      class="flex h-[72px] flex-col items-center justify-center gap-1 select-none"
      aria-current={i === activeIdx ? 'page' : undefined}
    >
      <span
        class="grid h-7 w-7 place-items-center transition-colors"
        class:text-Utility-orange={i === activeIdx}
        class:text-ink-500={i !== activeIdx}
      >
        <Icon size={22} strokeWidth={i === activeIdx ? 2.4 : 2} />
      </span>
      <span
        class="text-[10.5px] font-medium tracking-wide"
        class:text-Utility-orange={i === activeIdx}
        class:text-ink-500={i !== activeIdx}
      >
        {tab.label}
      </span>
    </a>
  {/each}
</nav>
