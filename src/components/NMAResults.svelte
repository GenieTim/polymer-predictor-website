<script lang="ts">
  import {
    CategoryScale,
    Chart,
    Legend,
    LinearScale,
    LineController,
    LineElement,
    LogarithmicScale,
    PointElement,
    Title,
    Tooltip,
  } from "chart.js";
  import { onMount } from "svelte";
  import type { DynamicModulusPredictorOutput } from "../entity/PredictionOutput";
  import BaseResultCard from "./BaseResultCard.svelte";

  // Register Chart.js components
  Chart.register(
    CategoryScale,
    LinearScale,
    LogarithmicScale,
    PointElement,
    LineController,
    LineElement,
    Title,
    Tooltip,
    Legend
  );

  interface Props {
    result: DynamicModulusPredictorOutput | null;
    loading: boolean;
    dirty: boolean;
    error?: string | null;
  }

  let { result, loading, dirty, error = null }: Props = $props();

  // Chart controls
  let xScaling = $state(1);
  let yScaling = $state(1);
  let xMin = $state<number | null>(null);
  let xMax = $state<number | null>(null);
  let yMin = $state<number | null>(null);
  let yMax = $state<number | null>(null);

  let chartCanvas = $state<HTMLCanvasElement | undefined>();
  let chart: Chart | null = null;

  function initChart() {
    if (!result || !chartCanvas) return;

    // Clean up existing chart
    if (chart) {
      chart.destroy();
    }

    const frequencies = result.frequencies;
    const storageModulus = result.g_prime;
    const lossModulus = result.g_double_prime;

    // Filter and sort data for valid logarithmic plotting
    const storageModulusData = storageModulus
      .map((value, index) => ({ x: frequencies[index], y: value }))
      .filter(p => p.x > 0 && p.y > 0)
      .sort((a, b) => a.x - b.x);
    const lossModulusData = lossModulus
      .map((value, index) => ({ x: frequencies[index], y: value }))
      .filter(p => p.x > 0 && p.y > 0)
      .sort((a, b) => a.x - b.x);

    const ctx = chartCanvas.getContext("2d");
    if (!ctx) return;

    chart = new Chart(ctx, {
      type: "line",
      data: {
        datasets: [
          {
            label: "Storage Modulus (G')",
            data: storageModulusData,
            backgroundColor: "#1f77b4",
            borderColor: "#1f77b4",
            fill: false,
          },
          {
            label: "Loss Modulus (G'')",
            data: lossModulusData,
            backgroundColor: "#ff7f0e",
            borderColor: "#ff7f0e",
            fill: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            type: "logarithmic",
            position: "bottom",
            title: {
              display: true,
              text: "Frequency",
            },
          },
          y: {
            type: "logarithmic",
            title: {
              display: true,
              text: "Modulus",
            },
          },
        },
        plugins: {
          legend: {
            display: true,
          },
        },
      },
    });

    resetLimits();
  }

  function updateChart() {
    if (!chart || !result) return;

    const frequencies = result.frequencies;
    const storageModulus = result.g_prime;
    const lossModulus = result.g_double_prime;

    // Apply scaling
    const scaledFreq = frequencies.map((f) => f * xScaling);
    const scaledStorage = storageModulus.map((s) => s * yScaling);
    const scaledLoss = lossModulus.map((l) => l * yScaling);

    // Filter and sort scaled data
    const storageModulusData = scaledStorage
      .map((value, index) => ({ x: scaledFreq[index], y: value }))
      .filter(p => p.x > 0 && p.y > 0)
      .sort((a, b) => a.x - b.x);
    const lossModulusData = scaledLoss
      .map((value, index) => ({ x: scaledFreq[index], y: value }))
      .filter(p => p.x > 0 && p.y > 0)
      .sort((a, b) => a.x - b.x);

    chart.data.datasets[0].data = storageModulusData;
    chart.data.datasets[1].data = lossModulusData;

    // Update axis limits
    const options = chart.options.scales!;
    if (xMin !== null) options.x!.min = xMin;
    else delete options.x!.min;

    if (xMax !== null) options.x!.max = xMax;
    else delete options.x!.max;

    if (yMin !== null) options.y!.min = yMin;
    else delete options.y!.min;

    if (yMax !== null) options.y!.max = yMax;
    else delete options.y!.max;

    chart.update();
  }

  function resetLimits() {
    if (!result) return;

    const frequencies = result.frequencies;
    const storageModulus = result.g_prime;
    const lossModulus = result.g_double_prime;

    // Filter data for valid values
    const validStorage = storageModulus.filter((_, i) => frequencies[i] > 0 && storageModulus[i] > 0 && lossModulus[i] > 0);
    const validLoss = lossModulus.filter((_, i) => frequencies[i] > 0 && storageModulus[i] > 0 && lossModulus[i] > 0);
    const validFreq = frequencies.filter((f, i) => f > 0 && storageModulus[i] > 0 && lossModulus[i] > 0);

    // Calculate min/max values from the filtered dataset
    xMin = Math.min(...validFreq);
    xMax = Math.max(...validFreq);
    yMin = Math.min(...validStorage, ...validLoss);
    yMax = Math.max(...validStorage, ...validLoss);
    xScaling = 1;
    yScaling = 1;

    updateChart();
  }

  // Initialize chart when component mounts
  onMount(() => {
    return () => {
      // Cleanup on unmount
      if (chart) {
        chart.destroy();
      }
    };
  });

  // Reactive updates for chart initialization and updates
  $effect(() => {
    if (result && chartCanvas && !chart) {
      initChart();
    } else if (result && chart) {
      updateChart();
    }
  });

  // Reactive updates for scaling and limits
  $effect(() => {
    if (
      chart &&
      result &&
      (xScaling !== 1 ||
        yScaling !== 1 ||
        xMin !== null ||
        xMax !== null ||
        yMin !== null ||
        yMax !== null)
    ) {
      updateChart();
    }
  });
</script>

<BaseResultCard
  id="nma-results"
  title="Normal Mode Analysis"
  {loading}
  {dirty}
  {error}
  loadingText="Computing NMA..."
  emptyText="NMA result will appear here."
  hasResult={!!result}
>
  {#if result}
    <!-- Controls Section -->
    <div class="row mb-4">
      <div class="col-md-12">
        <h6>Scaling Factors</h6>
        <div class="row">
          <div class="col-6">
            <label for="xScaling" class="form-label">X-Axis Scale:</label>
            <input
              type="number"
              class="form-control"
              bind:value={xScaling}
              step="0.1"
              min="0.1"
            />
          </div>
          <div class="col-6">
            <label for="yScaling" class="form-label">Y-Axis Scale:</label>
            <input
              type="number"
              class="form-control"
              bind:value={yScaling}
              step="0.1"
              min="0.1"
            />
          </div>
        </div>
      </div>
    </div>

    <div class="row mb-4">
      <div class="col-md-12">
        <h6>Axis Limits</h6>
        <div class="row">
          <div class="col-3">
            <label for="xMin" class="form-label">X Min:</label>
            <input
              type="number"
              class="form-control"
              bind:value={xMin}
              step="any"
            />
          </div>
          <div class="col-3">
            <label for="xMax" class="form-label">X Max:</label>
            <input
              type="number"
              class="form-control"
              bind:value={xMax}
              step="any"
            />
          </div>
          <div class="col-3">
            <label for="yMin" class="form-label">Y Min:</label>
            <input
              type="number"
              class="form-control"
              bind:value={yMin}
              step="any"
            />
          </div>
          <div class="col-3">
            <label for="yMax" class="form-label">Y Max:</label>
            <input
              type="number"
              class="form-control"
              bind:value={yMax}
              step="any"
            />
          </div>
        </div>
      </div>
    </div>

    <div class="row mb-3">
      <div class="col">
        <button
          type="button"
          class="btn btn-secondary"
          onclick={resetLimits}>Reset Limits</button
        >
      </div>
    </div>

    <!-- Chart Container -->
    <div class="chart-container" style="position: relative; height: 500px;">
      <canvas bind:this={chartCanvas}></canvas>
    </div>
  {/if}
</BaseResultCard>

<style>
  .chart-container {
    position: relative;
    height: 500px;
    width: 100%;
  }
</style>
