<script lang="ts">
  import type { PredictionInput } from "../entity/PredictionInput";
  import type { ModulusPredictionOutput } from "../entity/PredictionOutput";
  import { myQtyFormatter } from "../utils/utils";
  import Badge from "./Badge.svelte";
  import BaseResultCard from "./BaseResultCard.svelte";
  import FormattedNumber from "./FormattedNumber.svelte";
  import ModulusCard from "./ModulusCard.svelte";

  interface Props {
    result: ModulusPredictionOutput | null;
    loading: boolean;
    dirty: boolean;
    error?: string | null;
    predictionInput: PredictionInput;
  }

  let { result, loading, dirty, error = null, predictionInput }: Props = $props();
</script>

<BaseResultCard
  id="mmt-results"
  title="MMT Prediction"
  {loading}
  {dirty}
  {error}
  loadingText="Computing MMT..."
  emptyText="MMT result will appear here."
  hasResult={!!result}
>
  {#if result}
    {#if !predictionInput.is_mmtable()}
      <div class="alert alert-warning">
        <small>
          <i class="fas fa-exclamation-triangle"></i>
          These input parameter are even less suitable for the Miller-Macosko
          theory. Please consider other models for more reliable results.
        </small>
      </div>
    {/if}
    
    <!-- Primary result -->
    <div class="text-center p-3 bg-secondary text-white rounded mb-3">
      <h3 class="mb-0">
        <i>G</i><sub>eq</sub> =
        <FormattedNumber value_with_unit={result.modulus} />
      </h3>
    </div>

    <!-- Detailed breakdown -->
    <div class="row mb-3">
      <div class="col-6">
        <ModulusCard
          label="Phantom"
          value_with_unit={result.phantom_modulus}
          variant="light"
        />
      </div>
      <div class="col-6">
        <ModulusCard
          label="Entangled"
          value_with_unit={result.entanglement_modulus}
          variant="light"
        />
      </div>
    </div>

    <!-- Weight fractions -->
    <div class="border-top pt-3">
      <h6 class="text-muted mb-2">Weight Fractions</h6>
      <div class="row">
        <div class="col-sm-4">
          <Badge
            label="w<sub>soluble</sub>"
            value={result.w_soluble.format(myQtyFormatter)}
            title={result.w_soluble.toString()}
          />
        </div>
        <div class="col-sm-4">
          <Badge
            label="w<sub>dangling</sub>"
            value={result.w_dangling.format(myQtyFormatter)}
            title={result.w_dangling.toString()}
          />
        </div>
        <div class="col-sm-4">
          <Badge
            label="w<sub>backbone</sub>"
            value={result.w_active.format(myQtyFormatter)}
            title={result.w_active.toString()}
          />
        </div>
      </div>
    </div>
  {/if}
</BaseResultCard>
