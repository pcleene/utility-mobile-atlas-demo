<script lang="ts">
  import type { BillStatus, OutageStatus } from '$lib/types';

  let {
    status,
    overdueDays
  }: {
    status: BillStatus | OutageStatus | string;
    overdueDays?: number | null;
  } = $props();

  const cls = $derived.by(() => {
    switch (status) {
      case 'PAID':
        return 'pill-success';
      case 'UNPAID':
        return 'pill-orange';
      case 'OVERDUE':
        return 'pill-danger';
      case 'ACTIVE':
      case 'INVESTIGATING':
        return 'pill-danger';
      case 'RESTORING':
        return 'pill-warning';
      case 'RESOLVED':
        return 'pill-success';
      default:
        return 'pill-muted';
    }
  });

  const label = $derived.by(() => {
    if (status === 'UNPAID' && overdueDays != null && overdueDays < 0) {
      return `Overdue ${Math.abs(overdueDays)}d`;
    }
    if (status === 'UNPAID' && overdueDays != null && overdueDays <= 5) {
      return `Due in ${overdueDays}d`;
    }
    return String(status).replace('_', ' ');
  });
</script>

<span class="pill {cls}">{label}</span>
