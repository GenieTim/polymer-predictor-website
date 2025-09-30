<script lang="ts">
  interface Props {
    label: string;
    value: string;
    error?: string;
    unit?: string;
    variant?: "primary" | "secondary" | "light";
  }

  let { label, value, error, unit, variant = "light" }: Props = $props();
</script>

<div class="text-center p-2 bg-{variant} rounded">
  <small class="text-muted d-block">{label}</small>
  <strong>{value}</strong>
  {#if error}<span class="error">± {error}</span>{/if}
  {#if unit}<small class="text-muted unit">{unit}</small>{/if}
</div>
