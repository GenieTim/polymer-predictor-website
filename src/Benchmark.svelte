<script lang="ts">
  import { onMount } from "svelte";
  import {
    asyncRun,
    getWorkerPoolMetrics,
    whenPoolReady,
    type WorkerPoolMetrics,
  } from "./workerApi";

  interface SolverBenchRow {
    solver: string;
    simplification: string;
    durationMs: number | null;
    modulusMPa: number | null;
    status: string;
  }

  let poolMetrics = $state<WorkerPoolMetrics>(getWorkerPoolMetrics());
  let roundtripMs = $state<number | null>(null);
  let solverRunning = $state(false);
  let solverError = $state<string | null>(null);
  let solverRows = $state<SolverBenchRow[]>([]);
  let nChains = $state(400);

  const benchmarkScript = `
import json
import math
import time
import numpy as np
from pint import UnitRegistry
from pylimer_tools.generate_network import prepare_structure_generation
from pylimer_tools.io.bead_spring_parameter_provider import get_gaussian_parameters_for_polymer
from pylimer_tools_cpp import SLESolver, StructureSimplificationMode

ureg = UnitRegistry()
params = get_gaussian_parameters_for_polymer("PDMS", ureg=ureg)

universe_gen = prepare_structure_generation(
    params=params,
    n_beads_per_chain_1=50,
    n_chains_1=int(n_chains),
    n_mono_beads_per_chain=10,
    n_mono_chains=0,
    target_f=4,
    target_p=0.95,
    n_solvent_chains=0,
    n_beads_per_solvent_chain=1,
    n_beads_per_xlink=1,
    remove_wsol=False,
    disable_primary_loops=False,
    disable_secondary_loops=False,
    functionalize_discrete=False,
    n_chains_crosslinkers=int(n_chains // 2),
)

volume = universe_gen.get_box().get_volume()
entanglement_density = params.get_entanglement_density(params.get("Ge"))
n_entanglements = int(entanglement_density * volume)
kbt = 298.15 * ureg.kelvin * params.get("kb")
gamma_conv = (kbt / ((params.get("distance_units")) ** 3)).to("MPa").magnitude
r02_slope_mag = params.get("R02").to("nm^2").magnitude
cutoff_mag = (2.0 * ureg("nm")).to(params.get("distance_units")).magnitude

solver_names = list(SLESolver.__members__.keys())

configs = [
    ("NO_SIMPLIFICATION", StructureSimplificationMode.NO_SIMPLIFICATION),
    ("INACTIVE_THEN_X2F", StructureSimplificationMode.INACTIVE_THEN_X2F),
]

rows = []
for simp_name, simp_mode in configs:
    for s_name in solver_names:
        if not hasattr(SLESolver, s_name):
            rows.append({
                "solver": s_name,
                "simplification": simp_name,
                "durationMs": None,
                "modulusMPa": None,
                "status": "unavailable",
            })
            continue
        solver_enum = getattr(SLESolver, s_name)
        try:
            t0 = time.perf_counter()
            if n_entanglements > 0:
                fb = universe_gen.get_force_balance2(
                    nr_of_entanglements_to_sample=n_entanglements,
                    upper_cutoff=cutoff_mag,
                    lower_cutoff=0.0,
                    minimum_nr_of_entanglements=int(math.floor(n_entanglements * 0.95)),
                    same_strand_cutoff=0.0,
                    seed="bench_seed",
                    entanglements_as_springs=False,
                    crosslinker_type=2,
                )
            else:
                fb = universe_gen.get_force_balance2()
            fb.run_force_relaxation(
                simplification_mode=simp_mode,
                sle_solver=solver_enum,
            )
            g_val = float(gamma_conv * np.sum(fb.get_gamma_factors(r02_slope_mag)) / volume)
            dt_ms = (time.perf_counter() - t0) * 1000.0
            rows.append({
                "solver": s_name,
                "simplification": simp_name,
                "durationMs": round(dt_ms, 2),
                "modulusMPa": round(g_val, 6),
                "status": "ok",
            })
        except Exception as exc:
            rows.append({
                "solver": s_name,
                "simplification": simp_name,
                "durationMs": None,
                "modulusMPa": None,
                "status": f"error: {exc}",
            })

json.dumps(rows)
`;

  onMount(() => {
    const interval = setInterval(() => {
      poolMetrics = getWorkerPoolMetrics();
      if (poolMetrics.allReady) {
        clearInterval(interval);
      }
    }, 100);

    whenPoolReady().then(async (metrics) => {
      poolMetrics = metrics;
      const t0 = performance.now();
      await asyncRun("1 + 1", {});
      roundtripMs = performance.now() - t0;
    });

    return () => clearInterval(interval);
  });

  async function runSolverBenchmark() {
    solverRunning = true;
    solverError = null;
    solverRows = [];
    try {
      const res = await asyncRun(benchmarkScript, { n_chains: nChains });
      const raw = res.result ?? res;
      solverRows = (typeof raw === "string" ? JSON.parse(raw) : raw) as SolverBenchRow[];
    } catch (err) {
      solverError = err instanceof Error ? err.message : String(err);
    } finally {
      solverRunning = false;
    }
  }
</script>

<main class="container py-4">
  <h1 class="mb-3">Pyodide &amp; MEHPForceBalance2 Benchmark</h1>

  <section class="card p-3 mb-4">
    <h2 class="h5">1. Worker Pool Startup Latency</h2>
    <p class="mb-2">
      Initialized: <strong>{poolMetrics.initializedCount} / {poolMetrics.poolSize}</strong>
      {#if poolMetrics.firstReadyAt !== null}
        | First worker ready: <strong>{(poolMetrics.firstReadyAt - poolMetrics.poolCreatedAt).toFixed(0)} ms</strong>
      {/if}
      {#if poolMetrics.allReadyAt !== null}
        | All workers ready: <strong>{(poolMetrics.allReadyAt - poolMetrics.poolCreatedAt).toFixed(0)} ms</strong>
      {/if}
      {#if roundtripMs !== null}
        | Warm <code>asyncRun</code> roundtrip: <strong>{roundtripMs.toFixed(1)} ms</strong>
      {/if}
    </p>
    <table class="table table-sm mb-0">
      <thead>
        <tr>
          <th>Worker</th>
          <th>Status</th>
          <th>Wall Init (ms)</th>
          <th>In-Worker Init (ms)</th>
        </tr>
      </thead>
      <tbody>
        {#each poolMetrics.workers as w}
          <tr>
            <td>#{w.index}</td>
            <td>{w.isInitialized ? "Ready" : "Initializing..."}</td>
            <td>{w.wallInitMs !== null ? w.wallInitMs.toFixed(0) : "-"}</td>
            <td>{w.workerInitDurationMs !== null ? w.workerInitDurationMs.toFixed(0) : "-"}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </section>

  <section class="card p-3">
    <h2 class="h5">2. MEHPForceBalance2 Solver Benchmark (WASM)</h2>
    <div class="d-flex align-items-center gap-2 mb-3">
      <label class="form-label mb-0" for="n-chains">Chains:</label>
      <input
        id="n-chains"
        type="number"
        class="form-control w-auto"
        min="50"
        max="5000"
        step="50"
        bind:value={nChains}
      />
      <button
        class="btn btn-primary"
        disabled={solverRunning}
        onclick={runSolverBenchmark}
      >
        {solverRunning ? "Running benchmark..." : "Run Solver Benchmark"}
      </button>
    </div>

    {#if solverError}
      <div class="alert alert-danger">{solverError}</div>
    {/if}

    {#if solverRows.length > 0}
      <table class="table table-sm table-striped mb-0">
        <thead>
          <tr>
            <th>Simplification</th>
            <th>SLESolver</th>
            <th>Duration (ms)</th>
            <th>G (MPa)</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {#each solverRows as row}
            <tr>
              <td><code>{row.simplification}</code></td>
              <td><code>{row.solver}</code></td>
              <td>{row.durationMs !== null ? row.durationMs.toFixed(2) : "-"}</td>
              <td>{row.modulusMPa !== null ? row.modulusMPa.toFixed(6) : "-"}</td>
              <td>{row.status}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </section>
</main>
