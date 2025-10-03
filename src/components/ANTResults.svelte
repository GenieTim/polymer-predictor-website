<script lang="ts">
  import type { ModulusPredictionOutput } from "../entity/PredictionOutput";
  import Badge from "./Badge.svelte";
  import BaseResultCard from "./BaseResultCard.svelte";
  import FormattedNumber from "./FormattedNumber.svelte";
  import ModulusCard from "./ModulusCard.svelte";
  import { format2, mean, std } from "../utils/utils";
  import Qty from "js-quantities";

  interface Props {
    samples: ModulusPredictionOutput[];
    loading: boolean;
    dirty: boolean;
    error?: string | null;
  }

  let { samples, loading, dirty, error = null }: Props = $props();

  function computeAntAggregate(samples: ModulusPredictionOutput[]) {
    if (!samples.length) return null;

    const phantomVals = samples.map((s) => s.phantom_modulus.scalar);
    const entangledVals = samples.map((s) => s.entanglement_modulus.scalar);
    const eqVals = samples.map(
      (s) => s.phantom_modulus.scalar + s.entanglement_modulus.scalar
    );
    const w_solubleVals = samples.map((s) => s.w_soluble.scalar);
    const w_danglingVals = samples.map((s) => s.w_dangling.scalar);

    return {
      n: samples.length,
      phantom_mean: mean(phantomVals),
      phantom_std: std(phantomVals),
      entangled_mean: mean(entangledVals),
      entangled_std: std(entangledVals),
      eq_mean: mean(eqVals),
      eq_std: std(eqVals),
      w_soluble_mean: mean(w_solubleVals),
      w_dangling_mean: mean(w_danglingVals),
      w_backbone_mean: 1 - mean(w_solubleVals) - mean(w_danglingVals),
    };
  }

  let antAggregate = $derived(computeAntAggregate(samples));
</script>

<BaseResultCard
  id="ant-results"
  title="ANT Estimates"
  {loading}
  {dirty}
  {error}
  loadingText="Computing ANT..."
  emptyText="ANT results will appear here."
  hasResult={!!antAggregate}
>
  {#if antAggregate}
    <div class="text-center p-3 bg-success text-white rounded mb-3">
      <h3 class="mb-0">
        <i>G</i><sub>eq</sub> =
        <FormattedNumber
          value={antAggregate.eq_mean}
          std_deviation={antAggregate.eq_std}
          unit="MPa"
        />
      </h3>
    </div>

    <div class="row mb-3">
      <div class="col-6">
        <ModulusCard
          label="Phantom"
          value_with_unit={Qty(antAggregate.phantom_mean, "MPa")}
          error={antAggregate.phantom_std}
        />
      </div>
      <div class="col-6">
        <ModulusCard
          label="Entangled"
          value_with_unit={Qty(antAggregate.entangled_mean, "MPa")}
          error={antAggregate.entangled_std}
        />
      </div>
    </div>

    <div class="border-top pt-3">
      <h6 class="text-muted mb-2">Weight Fractions</h6>
      <div class="row">
        <div class="col-sm-4">
          <Badge
            label="w<sub>soluble</sub>"
            value={format2(antAggregate.w_soluble_mean)}
            title="soluble"
          />
        </div>
        <div class="col-sm-4">
          <Badge
            label="w<sub>dangling</sub>"
            value={format2(antAggregate.w_dangling_mean)}
            title="dangling"
          />
        </div>
        <div class="col-sm-4">
          <Badge
            label="w<sub>backbone</sub>"
            value={format2(antAggregate.w_backbone_mean)}
            title="backbone"
          />
        </div>
      </div>
    </div>
  {/if}
</BaseResultCard>
