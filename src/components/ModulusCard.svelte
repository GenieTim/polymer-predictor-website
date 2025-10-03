<script lang="ts">
  import type Qty from "js-quantities";
  import FormattedNumber from "./FormattedNumber.svelte";

  interface Props {
    label: string;
    value_with_unit: Qty;
    error?: number;
    variant?: "primary" | "secondary" | "light";
  }

  let { label, value_with_unit, error, variant = "light" }: Props = $props();
</script>

<div class="text-center p-2 bg-{variant} rounded">
  <small class="text-muted d-block">{label}</small>
  <FormattedNumber {value_with_unit} std_deviation={error} />
</div>
