<script lang="ts">
  import { formatNumberWithErrorAndUnit } from '../utils/FormattedNumber.utils';

  interface Props {
    value: number;
    std_deviation: number;
    decimals?: number | null;
    unit?: string;
  }

  let { value, std_deviation, decimals = null, unit = "" }: Props = $props();

  const formatted = $derived.by(() => formatNumberWithErrorAndUnit(value, std_deviation, decimals, unit));
</script>

<span class="formatted-number">
  <strong>{formatted.value}</strong>
  {#if formatted.error}
    <span class="error">± {formatted.error}</span>
  {/if}
  {#if formatted.unit}
    <span class="unit text-muted">{formatted.unit}</span>
  {/if}
</span>
