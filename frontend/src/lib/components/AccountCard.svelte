<script lang="ts">
  import type { Account } from '$lib/types';
  import { maskAccountNo } from '$lib/format';

  let {
    account,
    selected = false,
    onclick
  }: {
    account: Account;
    selected?: boolean;
    onclick?: () => void;
  } = $props();
</script>

<button
  type="button"
  class="card-press shrink-0 snap-center text-left transition-shadow"
  style:width="280px"
  {onclick}
>
  <div
    class="card flex h-[140px] flex-col justify-between p-4 transition-all"
    class:ring-2={selected}
    class:ring-Utility-orange={selected}
    class:ring-offset-1={selected}
    style:box-shadow={selected ? 'var(--shadow-pop)' : undefined}
  >
    <div class="flex items-start justify-between">
      <div class="min-w-0">
        <div class="truncate text-[15px] font-semibold text-ink-900">
          {account.nickname}
        </div>
        <div class="tnum mt-0.5 text-[13px] text-ink-500">
          {maskAccountNo(account.account_no)}
        </div>
      </div>
      <span
        class="pill {account.relationship === 'OWNER'
          ? 'pill-blue'
          : 'pill-muted'}"
      >
        {account.relationship}
      </span>
    </div>
    <div class="space-y-0.5">
      <div class="line-clamp-1 text-[12.5px] text-ink-700">
        {account.address.line1}
      </div>
      <div class="line-clamp-1 text-[12px] text-ink-500">
        {account.address.city}, {account.address.state}
      </div>
    </div>
    <div class="flex items-center justify-between">
      <span class="text-[11px] text-ink-500"
        >{account.tariff_scheme} · {account.customer_class}</span
      >
      <span class="text-[10px] font-semibold tracking-wider text-ink-300"
        >UtilityApp</span
      >
    </div>
  </div>
</button>
