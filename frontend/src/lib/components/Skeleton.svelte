<script lang="ts">
  let {
    width = '100%',
    height = '1rem',
    rounded = '8px',
    class: cls = ''
  }: {
    width?: string;
    height?: string;
    rounded?: string;
    class?: string;
  } = $props();
</script>

<div
  class="skeleton {cls}"
  style:width
  style:height
  style:border-radius={rounded}
></div>
