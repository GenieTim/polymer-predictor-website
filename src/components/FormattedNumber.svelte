<script lang="ts">
  import type Qty from "js-quantities";
  import { formatNumberWithErrorAndUnit } from "../utils/FormattedNumber.utils";
  import { jsonFormatter, myQtyFormatter } from "../utils/utils";

  interface Props {
    value?: number;
    value_with_unit?: Qty;
    std_deviation?: number;
    decimals?: number;
    unit?: string;
  }

  let {
    value,
    value_with_unit,
    std_deviation,
    decimals = undefined,
    unit = "",
  }: Props = $props();

  const formatted = $derived.by(() => {
    console.log("FormattedNumber props:", {
      value,
      value_with_unit,
      std_deviation,
      decimals,
      unit,
    });
    return value !== undefined
      ? formatNumberWithErrorAndUnit(value, std_deviation, decimals, unit)
      : value_with_unit
        ? formatNumberWithErrorAndUnit(
            JSON.parse(value_with_unit.format(jsonFormatter)).scalar,
            std_deviation,
            decimals,
            JSON.parse(value_with_unit.format(jsonFormatter)).unit
          )
        : { value: "N/A", error: null, unit: "" };
  });
</script>

<span class="formatted-number">
  <strong
    title={value
      ? value.toLocaleString() + " " + unit
      : value_with_unit
        ? value_with_unit.format(myQtyFormatter)
        : "N/A"}>{formatted.value}</strong
  >
  {#if formatted.error && std_deviation !== undefined}
    <span class="error" title={std_deviation.toLocaleString() + " " + unit}>
      ± {formatted.error}
    </span>
  {/if}
  {#if formatted.unit}
    <span class="unit text-muted">{formatted.unit}</span>
  {/if}
</span>
