<script lang="ts">
	/**
	 * Port of the legacy Django template (old.html) to Svelte.
	 * Replaces server POST endpoints with local web‑worker predictors.
	 */
	import { PredictionInput } from "./entity/PredictionInput";
	import type { DynamicModulusPredictorOutput, ModulusPredictionOutput } from "./entity/PredictionOutput";
	import type { Quantity } from "./entity/Quantity";
	import { ANTPredictor } from "./worker_predictor/ant/ant_predictor";
	import { MMTPredictor } from "./worker_predictor/mmt/mmt_predictor";
	import { NMAPredictor } from "./worker_predictor/nma/nma_predictor";
  import polymerPresetsDict from "../public/polymer-presets.json";

	// ---- Polymer definitions (placeholder until dynamic source added) ----
	interface PolymerPreset {
		name: string;
		temperature: number; // K
		density: number; // kg/cm^3
		plateau_modulus: number; // MPa
		bead_mass: number; // kg/mol
		mean_squared_bead_distance: number; // nm^2
		entanglement_sampling_cutoff: number; // nm
	}

	const polymerPresets: PolymerPreset[] = Object.values(polymerPresetsDict);

	// Selected polymer
	let polymer_name = polymerPresets[0].name;
	$: selectedPolymer = polymerPresets.find(p => p.name === polymer_name)!;

	// ---- Network parameter inputs (user editable) ----
	let stoichiometric_imbalance = 1.0; // r
	let crosslink_functionality = 4; // f
	let crosslink_conversion = 0.95; // p (will be clamped by reactive min/max)
	let b2_molar_fraction = 1.0; // b2

	// Molecular weights (user editable, converted to bead counts)
	let mw_bifunctional = 30 * selectedPolymer.bead_mass;
	let mw_monofunctional = 0;
	let mw_xlinks = 1 * selectedPolymer.bead_mass;
	let mw_zerofunctional = 0; // hidden

	// Additional synthesis parameters (booleans)
	let extract_solvent_before_measurement = false;
	let disable_primary_loops = false;
	let disable_secondary_loops = false;
	let functionalize_discrete = false;

	// Metadata
	let description = "";

	// Derived chain counts from b2 fraction (keep total constant like original JS: 1e4)
	const TOTAL_CHAINS = 10000;
	function computeChainNumbers(b2: number) {
		if (b2 <= 0) return { n_bifunctional_chains: 0, n_monofunctional_chains: TOTAL_CHAINS };
		const n_bifunctional_chains = Math.round((b2 * TOTAL_CHAINS) / (2 - b2));
		const n_monofunctional_chains = TOTAL_CHAINS - n_bifunctional_chains;
		return { n_bifunctional_chains, n_monofunctional_chains };
	}
	$: ({ n_bifunctional_chains, n_monofunctional_chains } = computeChainNumbers(b2_molar_fraction));
	const n_zerofunctional_chains = 0; // hidden & fixed

	// Reactive min/max for crosslink conversion p
	let pMin = 0.0;
	let pMax = 1.0;
	$: {
		// p_gel = sqrt( 1 / (r*(f-1)*b2) )
		const denom = stoichiometric_imbalance * (crosslink_functionality - 1) * b2_molar_fraction;
		let pgel = denom > 0 ? Math.sqrt(1 / denom) : 1;
		if (!isFinite(pgel)) pgel = 1;
		pMin = clamp(toStep(pgel, 0.01, "up"), 0, 1);

		// p_max logic from legacy JS:
		const max_possible_bonds = n_bifunctional_chains * 2 + n_monofunctional_chains;
		const n_xlinks = (max_possible_bonds * stoichiometric_imbalance) / crosslink_functionality;
		const p_max_calc = n_xlinks > 0 ? max_possible_bonds / (n_xlinks * crosslink_functionality) : 1;
		pMax = clamp(toStep(Math.min(1, p_max_calc), 0.01, "down"), 0, 1);
		// Clamp user input
		crosslink_conversion = clamp(crosslink_conversion, pMin, pMax);
	}

	function toStep(value: number, step: number, dir: "up" | "down") {
		return dir === "up" ? Math.ceil(value / step) * step : Math.floor(value / step) * step;
	}
	function clamp(v: number, min: number, max: number) { return Math.min(Math.max(v, min), max); }

	// Adjust crosslink functionality max based on n_beads_xlinks (legacy behavior)
	$: bead_mass = selectedPolymer.bead_mass;
	$: n_beads_xlinks = Math.max(1, Math.round(mw_xlinks / bead_mass));
	$: max_crosslink_functionality = Math.max(6, n_beads_xlinks * 6);
	$: crosslink_functionality = Math.min(crosslink_functionality, max_crosslink_functionality);

	// Convert molecular weights to bead numbers
	$: n_beads_bifunctional = Math.round(mw_bifunctional / bead_mass);
	$: n_beads_monofunctional = Math.round(mw_monofunctional / bead_mass);
	$: n_beads_zerofunctional = Math.round(mw_zerofunctional / bead_mass);

	// Form dirtiness / stale results marker
	let dirty = false;
	function markDirty() { dirty = true; }

	// Predictor instances (lazily created on first run to avoid spawning workers unnecessarily)
	let antPredictor: ANTPredictor | null = null;
	let mmtPredictor: MMTPredictor | null = null;
	let nmaPredictor: NMAPredictor | null = null;

	// Results & loading flags
	let antSamples: ModulusPredictionOutput[] = [];
	let antLoading = false;
	let mmtResult: ModulusPredictionOutput | null = null;
	let mmtLoading = false;
	let nmaResult: DynamicModulusPredictorOutput | null = null;
	let nmaLoading = false;

	// Aggregate ANT samples -> mean & (sample std as error)
	$: antAggregate = computeAntAggregate(antSamples);
	function computeAntAggregate(samples: ModulusPredictionOutput[]) {
		if (!samples.length) return null;
		function mean(vals: number[]) { return vals.reduce((a, b) => a + b, 0) / vals.length; }
		function std(vals: number[]) {
			if (vals.length < 2) return 0;
			const m = mean(vals);
			const v = vals.reduce((s, x) => s + (x - m) ** 2, 0) / (vals.length - 1);
			return Math.sqrt(v);
		}
		const phantomVals = samples.map(s => s.phantom_modulus.value);
		const entangledVals = samples.map(s => s.entanglement_modulus.value);
		const eqVals = samples.map(s => s.phantom_modulus.value + s.entanglement_modulus.value);
		const w_solubleVals = samples.map(s => s.w_soluble.value);
		const w_danglingVals = samples.map(s => s.w_dangling.value);
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

	function buildPredictionInput(): PredictionInput {
		// Build quantity helper
		const q = (value: number, unit: string): Quantity => ({ value, unit });
		return new PredictionInput({
			stoichiometric_imbalance,
			crosslink_conversion,
			crosslink_functionality,
			extract_solvent_before_measurement,
			disable_primary_loops,
			disable_secondary_loops,
			functionalize_discrete,
			n_zerofunctional_chains,
			n_monofunctional_chains,
			n_bifunctional_chains,
			n_beads_zerofunctional,
			n_beads_monofunctional,
			n_beads_bifunctional,
			n_beads_xlinks,
			temperature: q(selectedPolymer.temperature, "K"),
			density: q(selectedPolymer.density, "kg/cm^3"),
			bead_mass: q(selectedPolymer.bead_mass, "kg/mol"),
			mean_squared_bead_distance: q(selectedPolymer.mean_squared_bead_distance, "nm^2"),
			plateau_modulus: q(selectedPolymer.plateau_modulus, "MPa"),
			entanglement_sampling_cutoff: q(selectedPolymer.entanglement_sampling_cutoff, "nm"),
			description,
			polymer_name,
		});
	}

	async function runMMT(input: PredictionInput) {
		mmtLoading = true; mmtResult = null;
		mmtPredictor ||= new MMTPredictor();
		try { mmtResult = await mmtPredictor.predict(input); } finally { mmtLoading = false; }
	}

	async function runNMA(input: PredictionInput) {
		nmaLoading = true; nmaResult = null;
		nmaPredictor ||= new NMAPredictor();
		try { nmaResult = await nmaPredictor.predict(input); } finally { nmaLoading = false; }
	}

	async function runANTSample(input: PredictionInput) {
		antLoading = true;
		antPredictor ||= new ANTPredictor();
		try {
			const sample = await antPredictor.predict(input);
			antSamples = [...antSamples, sample];
		} finally {
			antLoading = false;
		}
	}

	async function onSubmit(ev: Event) {
		ev.preventDefault();
		dirty = false;
		antSamples = []; // reset previous samples on new submission
		const input = buildPredictionInput();
		// Launch predictors (ANT one sample first, others once)
		await Promise.all([
			runANTSample(input),
			runMMT(input),
			runNMA(input),
		]);
	}

	async function refineANT() {
		if (dirty) return; // avoid refining outdated input
		const input = buildPredictionInput();
		await runANTSample(input);
	}

	function format2(v?: number) { return v == null || !isFinite(v) ? "-" : v.toFixed(2); }
</script>

<style>
	.not-current { opacity: 0.5; filter: grayscale(40%); }
	.prediction-cards > div { margin-bottom: 1rem; }
	.error { color: #dc3545; font-size: 0.9em; margin-left: .25rem; }
	.unit { margin-left: .25rem; font-size: 0.85em; }
	details summary { cursor: pointer; }
	.card { border: 1px solid var(--hm-border-color, #ccc); border-radius: .5rem; }
	.card-header { padding: .75rem 1rem; border-bottom: 1px solid var(--hm-border-color, #ccc); background: var(--hm-card-header-bg, #f7f7f9); }
	.card-body { padding: 1rem; }
	.badge { display: inline-block; padding: .35em .6em; border-radius: .5rem; background: #6c757d; color: #fff; font-size: .75rem; }
	form h3 { margin-top: 1.5rem; }
	.btn + .btn { margin-left: .5rem; }
</style>

<div class="container">
	<div class="row">
		<div class="column col-sm-6">
			<h2>Input</h2>
			<form on:submit|preventDefault={onSubmit} id="prediction-form">
				<section>
					<h3>Polymer Properties</h3>
					<label>Polymer
						<select bind:value={polymer_name} class="form-select" on:change={() => { markDirty(); /* update dependent defaults */ mw_bifunctional = 30 * selectedPolymer.bead_mass; mw_xlinks = 1 * selectedPolymer.bead_mass; }}>
							{#each polymerPresets as p}
								<option value={p.name}>{p.name}</option>
							{/each}
						</select>
					</label>

					<details>
						<summary>Details</summary>
						<div class="row g-2 mt-2">
							<div class="col-6">
								<label class="w-100">T [K]
									<input class="form-control" value={selectedPolymer.temperature} readonly>
								</label>
							</div>
							<div class="col-6">
								<label class="w-100">ρ [kg/cm³]
									<input class="form-control" value={selectedPolymer.density} readonly>
								</label>
							</div>
							<div class="col-6">
								<label class="w-100">G<sub>e</sub>(1) [MPa]
									<input class="form-control" value={selectedPolymer.plateau_modulus} readonly>
								</label>
							</div>
							<div class="col-6">
								<label class="w-100">M<sub>w</sub> [kg/mol]
									<input class="form-control" value={selectedPolymer.bead_mass} readonly>
								</label>
							</div>
							<div class="col-6">
								<label class="w-100">⟨b²⟩ [nm²]
									<input class="form-control" value={selectedPolymer.mean_squared_bead_distance} readonly>
								</label>
							</div>
							<div class="col-6">
								<label class="w-100">s<sub>c</sub> [nm]
									<input class="form-control" value={selectedPolymer.entanglement_sampling_cutoff} readonly>
								</label>
							</div>
						</div>
					</details>
				</section>

				<hr />

				<section>
					<h3>Network Parameters</h3>
					<label class="w-100">Stoichiometric imbalance (r)
						<input type="number" step="0.01" min="0.5" max="2" bind:value={stoichiometric_imbalance} class="form-control" on:input={markDirty}>
					</label>
								<label class="w-100">Cross-link functionality (f) (≤ {max_crosslink_functionality})
									<input type="number" min="3" max={max_crosslink_functionality} bind:value={crosslink_functionality} class="form-control" on:input={markDirty}>
					</label>
					<label class="w-100">Cross-link conversion (p) [{format2(pMin)} – {format2(pMax)}]
						<input type="number" step="0.01" min={pMin} max={pMax} bind:value={crosslink_conversion} class="form-control" on:input={markDirty}>
					</label>
					<label class="w-100">b<sub>2</sub> molar fraction
						<input type="number" step="0.01" min="0" max="1" bind:value={b2_molar_fraction} class="form-control" on:input={markDirty}>
					</label>
					<label class="w-100">M<sub>w</sub><sup>B<sub>2</sub></sup> [kg/mol]
						<input type="number" step="0.0001" min="0.1" bind:value={mw_bifunctional} class="form-control" on:input={markDirty}>
					</label>
					<label class="w-100">M<sub>w</sub><sup>B<sub>1</sub></sup> [kg/mol]
						<input type="number" step="0.0001" min="0" bind:value={mw_monofunctional} class="form-control" on:input={markDirty}>
					</label>
					<label class="w-100">M<sub>w</sub><sup>X</sup> [kg/mol]
						<input type="number" step="0.0001" min="0.1" bind:value={mw_xlinks} class="form-control" on:input={markDirty}>
					</label>
				</section>

				<hr />

				<section>
					<h3>Additional Synthesis Parameters</h3>
					<label class="form-check d-block">
						<input type="checkbox" class="form-check-input" bind:checked={extract_solvent_before_measurement} on:change={markDirty}>
						Extract solvent before measurement
					</label>
					<label class="form-check d-block">
						<input type="checkbox" class="form-check-input" bind:checked={disable_primary_loops} on:change={markDirty}>
						Disable primary loops
					</label>
						<label class="form-check d-block">
							<input type="checkbox" class="form-check-input" bind:checked={disable_secondary_loops} on:change={markDirty}>
							Disable secondary loops
						</label>
						<label class="form-check d-block">
							<input type="checkbox" class="form-check-input" bind:checked={functionalize_discrete} on:change={markDirty}>
							Functionalize discrete
						</label>
				</section>

				<hr />

				<section>
					<label class="w-100">Description
						<textarea rows="3" class="form-control" bind:value={description} on:input={markDirty} placeholder="Optional description"></textarea>
					</label>
				</section>

				<hr />
				<div class="d-flex align-items-center gap-2">
					<button type="submit" class="btn btn-primary btn-lg">Predict</button>
					<button type="button" class="btn btn-outline-secondary" disabled={!antAggregate || dirty} on:click={refineANT}>Refine ANT</button>
					{#if antAggregate}
						<small class={dirty ? 'text-warning' : 'text-muted'}>{dirty ? 'Input changed – re-run Predict' : `ANT samples: ${antAggregate.n}`}</small>
					{/if}
				</div>
			</form>
		</div>

		<div class="column col-12 col-sm-6">
			<h2>Prediction</h2>
			<p>Choose parameters and click on "Predict". Results are computed locally in your browser.</p>
			<p class="text-muted">Predictions are model-based; validate critical decisions independently.</p>

			<div id="prediction-output" class="prediction-cards d-flex flex-column gap-3">
				<!-- ANT Results -->
				<div id="ant-results" class:not-current={dirty}>
					<div class="card">
						<div class="card-header"><h5 class="mb-0">ANT Estimates</h5></div>
						<div class="card-body">
							{#if antLoading && !antAggregate}
								<p>Computing ANT...</p>
							{:else if antAggregate}
								<div class="text-center p-3 bg-success text-white rounded mb-3">
									<h3 class="mb-0"><i>G</i><sub>eq</sub> = {format2(antAggregate.eq_mean)} {#if antAggregate.eq_std>0}<span class="error">± {format2(antAggregate.eq_std)}</span>{/if} <span class="unit">MPa</span></h3>
								</div>
								<div class="row mb-3">
									<div class="col-6">
										<div class="text-center p-2 bg-light rounded">
											<small class="text-muted d-block">Phantom</small>
											<strong>{format2(antAggregate.phantom_mean)}</strong>
											{#if antAggregate.phantom_std>0}<span class="error">± {format2(antAggregate.phantom_std)}</span>{/if}
											<small class="text-muted unit">MPa</small>
										</div>
									</div>
									<div class="col-6">
										<div class="text-center p-2 bg-light rounded">
											<small class="text-muted d-block">Entangled</small>
											<strong>{format2(antAggregate.entangled_mean)}</strong>
											{#if antAggregate.entangled_std>0}<span class="error">± {format2(antAggregate.entangled_std)}</span>{/if}
											<small class="text-muted unit">MPa</small>
										</div>
									</div>
								</div>
								<div class="border-top pt-3">
									<h6 class="text-muted mb-2">Weight Fractions</h6>
									<div class="row">
										<div class="col-sm-4"><span><i>w</i><sub>soluble</sub> = <span class="badge" title="soluble">{format2(antAggregate.w_soluble_mean)}</span></span></div>
										<div class="col-sm-4"><span><i>w</i><sub>dangling</sub> = <span class="badge" title="dangling">{format2(antAggregate.w_dangling_mean)}</span></span></div>
										<div class="col-sm-4"><span><i>w</i><sub>backbone</sub> = <span class="badge" title="backbone">{format2(antAggregate.w_backbone_mean)}</span></span></div>
									</div>
								</div>
								{#if antLoading}<p class="mt-2 text-muted">Refining...</p>{/if}
							{:else}
								<p>ANT results will appear here.</p>
							{/if}
						</div>
					</div>
				</div>

				<!-- MMT Results -->
				<div id="mmt-results" class:not-current={dirty}>
					<div class="card">
						<div class="card-header"><h5 class="mb-0">MMT Prediction</h5></div>
						<div class="card-body">
							{#if mmtLoading}
								<p>Computing MMT...</p>
							{:else if mmtResult}
								<p><strong>G<sub>eq</sub></strong>: {format2(mmtResult.phantom_modulus.value + mmtResult.entanglement_modulus.value)} MPa</p>
								<p class="mb-1"><small>Phantom: {format2(mmtResult.phantom_modulus.value)} MPa | Entangled: {format2(mmtResult.entanglement_modulus.value)} MPa</small></p>
								<p class="mb-0"><small>w<sub>soluble</sub>: {format2(mmtResult.w_soluble.value)} | w<sub>dangling</sub>: {format2(mmtResult.w_dangling.value)} | w<sub>backbone</sub>: {format2(1 - mmtResult.w_soluble.value - mmtResult.w_dangling.value)}</small></p>
							{:else}
								<p>MMT result will appear here.</p>
							{/if}
						</div>
					</div>
				</div>

				<!-- NMA (Dynamic Modulus) Results -->
				<div id="nma-results" class:not-current={dirty}>
					<div class="card">
						<div class="card-header"><h5 class="mb-0">NMA Dynamic Modulus</h5></div>
						<div class="card-body">
							{#if nmaLoading}
								<p>Computing NMA...</p>
							{:else if nmaResult}
								<p>Frequencies: {nmaResult.frequencies.length}</p>
								<p><small>First freq: {format2(nmaResult.frequencies[0])} | G' first: {format2(nmaResult.g_prime[0])}</small></p>
							{:else}
								<p>NMA result will appear here.</p>
							{/if}
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>
