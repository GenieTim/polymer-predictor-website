<script lang="ts">
  import type { ModulusPredictionOutput } from "../entity/PredictionOutput";
  import Badge from "./Badge.svelte";
  import BaseResultCard from "./BaseResultCard.svelte";
  import ModulusCard from "./ModulusCard.svelte";
  import { myQtyFormatter } from "../utils/utils";

  interface Props {
    result: ModulusPredictionOutput | null;
    loading: boolean;
    dirty: boolean;
    error?: string | null;
  }

  let { result, loading, dirty, error = null }: Props = $props();
</script>

<BaseResultCard
  id="nn-results"
  title="Neural Network Prediction"
  {loading}
  {dirty}
  {error}
  loadingText="Computing Neural Network..."
  emptyText="Neural Network result will appear here."
  hasResult={!!result}
>
  {#if result}
    <!-- Primary result -->
    <div class="text-center p-3 bg-info text-white rounded mb-3">
      <h3 class="mb-0">
        <i>G</i><sub>eq</sub> =
        <span title={result.modulus.toString()}
          >{result.modulus.format(myQtyFormatter)}</span
        >
      </h3>
    </div>

    <!-- Detailed breakdown -->
    <div class="row mb-3">
      <div class="col-6">
        <ModulusCard
          label="Phantom"
          value={result.phantom_modulus.format(myQtyFormatter)}
          variant="light"
        />
      </div>
      <div class="col-6">
        <ModulusCard
          label="Entangled"
          value={result.entanglement_modulus.format(myQtyFormatter)}
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
