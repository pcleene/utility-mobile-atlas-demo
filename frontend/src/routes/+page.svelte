<script lang="ts">
  import AppBar from '$lib/components/AppBar.svelte';
  import Skeleton from '$lib/components/Skeleton.svelte';
  import AccountCard from '$lib/components/AccountCard.svelte';
  import CurrentBillCard from '$lib/components/CurrentBillCard.svelte';
  import UsageGlanceCard from '$lib/components/UsageGlanceCard.svelte';
  import OutageBanner from '$lib/components/OutageBanner.svelte';
  import QuickActions from '$lib/components/QuickActions.svelte';
  import PromoStrip from '$lib/components/PromoStrip.svelte';
  import TimeBanner from '$lib/components/TimeBanner.svelte';
  import PaySheet from '$lib/components/PaySheet.svelte';
  import InspectableSection from '$lib/components/InspectableSection.svelte';
  import InspectOverlay from '$lib/components/InspectOverlay.svelte';
  import InspectButton from '$lib/components/InspectButton.svelte';
  import { api } from '$lib/api';
  import { session } from '$lib/stores.svelte';
  import { STATIC_INSPECT } from '$lib/staticInspect';
  import { timeOfDayGreeting } from '$lib/format';
  import type { Bill, DailyUsage, MongoInspect, Outage } from '$lib/types';

  let bills = $state<Bill[]>([]);
  let daily = $state<DailyUsage[]>([]);
  let outages = $state<Outage[]>([]);
  let loadingBill = $state(true);
  let loadingUsage = $state(true);
  let loadingOutage = $state(true);
  let showPay = $state(false);

  let inspectCustomer = $state<MongoInspect | null>(null);
  let inspectBill = $state<MongoInspect | null>(null);
  let inspectUsage = $state<MongoInspect | null>(null);
  let inspectOutage = $state<MongoInspect | null>(null);

  const greet = timeOfDayGreeting();
  const firstName = $derived(session.customer?.name?.split(' ')[0] ?? '');
  const currentBill = $derived<Bill | null>(
    bills.find((b) => b.status !== 'PAID') ?? bills[0] ?? null
  );

  $effect(() => {
    const acc = session.selectedAccount;
    if (!acc) return;
    void load(acc.account_no, acc.address?.location?.coordinates);
  });

  async function load(
    accountNo: string,
    coords?: [number, number] | null
  ): Promise<void> {
    loadingBill = true;
    loadingUsage = true;
    loadingOutage = true;
    try {
      const [b, d, o] = await Promise.all([
        api.bills(accountNo),
        api.usageDaily(accountNo, 14),
        coords
          ? api.outagesNearby(coords[0], coords[1])
          : Promise.resolve({ data: [] as Outage[], inspect: undefined })
      ]);
      bills = b.data;
      inspectBill = b.inspect ?? null;
      daily = d.data;
      inspectUsage = d.inspect ?? null;
      outages = o.data;
      inspectOutage = o.inspect ?? null;
    } finally {
      loadingBill = false;
      loadingUsage = false;
      loadingOutage = false;
    }
  }

  async function refresh() {
    const acc = session.selectedAccount;
    if (!acc) return;
    try {
      const me = await api.me();
      session.setCustomer(me.data);
      inspectCustomer = me.inspect ?? null;
    } catch {
      /* keep existing session */
    }
    void load(acc.account_no, acc.address?.location?.coordinates);
  }

  $effect(() => {
    if (session.customer && !inspectCustomer) {
      void api.me().then((r) => {
        inspectCustomer = r.inspect ?? null;
      });
    }
  });
</script>

<AppBar transparent>
  {#snippet rightSlot()}
    <button
      onclick={refresh}
      class="grid h-10 w-10 place-items-center rounded-full"
      aria-label="Refresh"
    >
      <span
        class="grid h-9 w-9 place-items-center rounded-full text-[13px] font-bold text-white"
        style:background={session.customer?.avatar_color ?? '#EE7A23'}
      >
        {firstName.slice(0, 1) || 'A'}
      </span>
    </button>
  {/snippet}
</AppBar>

<div class="fade-up flex flex-col gap-5 px-5 pt-1 pb-6">
  <div class="flex items-start justify-between gap-2">
    <div>
      <div class="text-[12.5px] font-medium text-ink-500">{greet.bm}</div>
      <h1 class="text-[26px] leading-tight font-bold tracking-tight">
        {greet.en}{firstName ? `, ${firstName}` : ''}
      </h1>
    </div>
    {#if inspectCustomer}
      <InspectButton inspect={inspectCustomer} label="Inspect customer query" />
    {/if}
  </div>

  <InspectableSection inspect={inspectCustomer} title="Linked accounts">
    <div class="-mx-5 overflow-hidden">
      <div class="no-scrollbar flex snap-x snap-mandatory gap-3 overflow-x-auto px-5">
        {#if !session.customer}
          {#each [0, 1] as _ (_)}
            <Skeleton width="280px" height="140px" rounded="20px" />
          {/each}
        {:else}
          {#each session.customer.accounts as acc (acc.account_no)}
            <AccountCard
              account={acc}
              selected={session.selectedAccountNo === acc.account_no}
              onclick={() => session.selectAccount(acc.account_no)}
            />
          {/each}
        {/if}
      </div>
    </div>
  </InspectableSection>

  <InspectableSection inspect={STATIC_INSPECT.timeBanner} title="Peak / off-peak">
    <TimeBanner />
  </InspectableSection>

  <section>
    {#if loadingBill}
      <Skeleton height="200px" rounded="20px" />
    {:else if currentBill}
      <InspectOverlay inspect={inspectBill}>
        <CurrentBillCard bill={currentBill} onPay={() => (showPay = true)} />
      </InspectOverlay>
    {:else}
      <div class="card flex items-center gap-3 p-5">
        <div class="text-[13px] text-ink-500">No bills issued yet for this account.</div>
      </div>
    {/if}
  </section>

  <section>
    {#if loadingOutage}
      <Skeleton height="74px" rounded="20px" />
    {:else}
      <InspectOverlay inspect={inspectOutage}>
        <OutageBanner {outages} />
      </InspectOverlay>
    {/if}
  </section>

  <section>
    {#if loadingUsage || daily.length === 0}
      <Skeleton height="220px" rounded="20px" />
    {:else}
      <InspectOverlay inspect={inspectUsage}>
        <UsageGlanceCard {daily} />
      </InspectOverlay>
    {/if}
  </section>

  <InspectableSection inspect={STATIC_INSPECT.quickActions} title="Quick actions">
    <QuickActions />
  </InspectableSection>

  <InspectableSection inspect={STATIC_INSPECT.promos} title="For you">
    <PromoStrip />
  </InspectableSection>
</div>

<PaySheet bill={currentBill} open={showPay} onClose={() => (showPay = false)} />
