<script lang="ts">
  import type { Outage } from '$lib/types';

  let { outages }: { outages: Outage[] } = $props();

  // Bounding box of Peninsular Malaysia (approx)
  const W = 320;
  const H = 220;
  const lngMin = 99.5,
    lngMax = 105.0;
  const latMin = 1.0,
    latMax = 7.0;

  function project(lng: number, lat: number): [number, number] {
    const x = ((lng - lngMin) / (lngMax - lngMin)) * W;
    const y = H - ((lat - latMin) / (latMax - latMin)) * H;
    return [x, y];
  }
</script>

<svg
  viewBox="0 0 {W} {H}"
  class="h-[220px] w-full rounded-2xl bg-Utility-blue-soft"
  role="img"
  aria-label="Map of Peninsular Malaysia with outage markers"
>
  <!-- Stylised peninsula silhouette — hand-drawn rough outline -->
  <path
    d="M155 14 C175 22 188 36 196 60 C210 80 220 96 222 116 C228 132 232 148 226 168 C218 184 198 196 178 198 C162 200 148 188 138 174 C126 162 116 148 110 132 C100 116 92 100 96 80 C100 60 116 38 132 24 C140 18 148 14 155 14 Z"
    fill="#fff"
    stroke="var(--color-Utility-blue)"
    stroke-width="1.4"
    stroke-linejoin="round"
    opacity="0.92"
  />
  <!-- East peninsula tail (Sabah/Sarawak hint) -->
  <path
    d="M236 132 C260 122 286 132 296 156 C300 168 290 178 274 178 C258 178 246 168 240 156 Z"
    fill="#fff"
    stroke="var(--color-Utility-blue)"
    stroke-width="1.4"
    stroke-linejoin="round"
    opacity="0.7"
  />

  <!-- Major city dots -->
  {#each [
    { name: 'KL', lng: 101.7, lat: 3.14 },
    { name: 'JB', lng: 103.75, lat: 1.47 },
    { name: 'Penang', lng: 100.32, lat: 5.41 },
    { name: 'Ipoh', lng: 101.1, lat: 4.6 }
  ] as c (c.name)}
    {@const [x, y] = project(c.lng, c.lat)}
    <circle cx={x} cy={y} r="2" fill="var(--color-ink-300)" />
    <text x={x + 5} y={y + 3} font-size="9" fill="var(--color-ink-500)">
      {c.name}
    </text>
  {/each}

  <!-- Active outages -->
  {#each outages as o (o.outage_id)}
    {@const [x, y] = project(
      o.affected.centroid.coordinates[0],
      o.affected.centroid.coordinates[1]
    )}
    <g>
      <circle
        cx={x}
        cy={y}
        r="14"
        fill="var(--color-Utility-orange)"
        opacity="0.18"
      >
        <animate
          attributeName="r"
          from="6"
          to="18"
          dur="1.6s"
          repeatCount="indefinite"
        />
        <animate
          attributeName="opacity"
          from="0.4"
          to="0"
          dur="1.6s"
          repeatCount="indefinite"
        />
      </circle>
      <circle cx={x} cy={y} r="4.5" fill="var(--color-Utility-orange)" />
      <circle cx={x} cy={y} r="2" fill="white" />
    </g>
  {/each}
</svg>
