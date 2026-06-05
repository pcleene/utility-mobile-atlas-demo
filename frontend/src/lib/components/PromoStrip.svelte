<script lang="ts">
  const promos = [
    {
      title: 'Cashback RM30 with JomPAY',
      sub: 'Pay your bill via JomPAY this month and get RM30 back.',
      gradient: 'from-Utility-orange to-[#FFB66E]',
      tag: 'BILL'
    },
    {
      title: 'EV Charging — Off-peak savings',
      sub: 'Charge between 10pm–8am for 14% lower energy rate.',
      gradient: 'from-Utility-blue to-[#4F7BC3]',
      tag: 'EV'
    },
    {
      title: 'myGreen+ subscription',
      sub: 'Offset your monthly footprint with Utility RECs.',
      gradient: 'from-success to-[#5BD389]',
      tag: 'GREEN'
    }
  ];
</script>

<div class="-mx-5 overflow-hidden">
  <div class="no-scrollbar flex snap-x snap-mandatory gap-3 overflow-x-auto px-5 pb-1">
    {#each promos as p (p.title)}
      <div
        class="snap-center bg-gradient-to-br {p.gradient} relative shrink-0 overflow-hidden rounded-[20px] p-4 text-white"
        style:width="240px"
        style:min-height="116px"
      >
        <span
          class="rounded-full bg-white/20 px-2 py-0.5 text-[10px] font-semibold tracking-widest"
        >
          {p.tag}
        </span>
        <div class="mt-2 text-[14px] font-semibold leading-snug">
          {p.title}
        </div>
        <div class="mt-1 line-clamp-2 text-[11.5px] leading-snug text-white/85">
          {p.sub}
        </div>
        <div
          class="absolute -right-6 -bottom-6 h-24 w-24 rounded-full bg-white/15 blur-2xl"
        ></div>
      </div>
    {/each}
  </div>
</div>
