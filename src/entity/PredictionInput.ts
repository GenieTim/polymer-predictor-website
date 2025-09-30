import Qty from "js-quantities";

export interface PredictionInputInit {
  stoichiometric_imbalance: number;
  crosslink_conversion: number;
  crosslink_functionality: number;

  extract_solvent_before_measurement?: boolean;
  disable_primary_loops?: boolean;
  disable_secondary_loops?: boolean;
  functionalize_discrete?: boolean;

  n_zerofunctional_chains: number;
  n_monofunctional_chains: number;
  n_bifunctional_chains: number;
  n_beads_zerofunctional: number;
  n_beads_monofunctional: number;
  n_beads_bifunctional: number;
  n_beads_xlinks?: number;

  temperature: Qty; // K
  density: Qty; // kg/cm^3
  bead_mass: Qty; // kg/mol
  mean_squared_bead_distance: Qty; // nm^2
  plateau_modulus: Qty; // MPa
  entanglement_sampling_cutoff: Qty; // nm

  description?: string;
  polymer_name?: string;
}

export class PredictionInput {
  // Synthesis parameters
  stoichiometric_imbalance!: number;
  crosslink_conversion!: number;
  crosslink_functionality!: number;

  extract_solvent_before_measurement = false;
  disable_primary_loops = false;
  disable_secondary_loops = false;
  functionalize_discrete = false;

  // Bead quantities
  n_zerofunctional_chains!: number;
  n_monofunctional_chains!: number;
  n_bifunctional_chains!: number;
  n_beads_zerofunctional!: number;
  n_beads_monofunctional!: number;
  n_beads_bifunctional!: number;
  n_beads_xlinks = 1;

  // Material & measurement properties
  temperature!: Qty;
  density!: Qty;
  bead_mass!: Qty;
  mean_squared_bead_distance!: Qty;
  plateau_modulus!: Qty;
  entanglement_sampling_cutoff!: Qty;

  // Additional Info (subset)
  description = "";
  polymer_name = "";

  constructor(init: PredictionInputInit) {
    Object.assign(this, init);
    // Apply defaults if undefined
    if (init.n_beads_xlinks !== undefined)
      this.n_beads_xlinks = init.n_beads_xlinks;
    this.extract_solvent_before_measurement ??= false;
    this.disable_primary_loops ??= false;
    this.disable_secondary_loops ??= false;
    this.functionalize_discrete ??= false;
    this.description ||= "";
    this.polymer_name ||= "";
  }

  // Computed values
  public get b2(): number {
    return (
      (this.n_bifunctional_chains * 2) /
      (this.n_bifunctional_chains * 2 + this.n_monofunctional_chains)
    );
  }

  public get mean_bead_distance(): Qty {
    // alpha = 3π/8; returns sqrt( <r^2> / alpha )
    const alpha = (3 * Math.PI) / 8.0;
    const val = Math.sqrt(this.mean_squared_bead_distance.to("nm^2").scalar / alpha);
    return Qty(val, "nm");
  }

  public get bead_density(): Qty {
    // density / bead_mass -> (kg/cm^3) / (kg/mol) = mol/cm^3
    // Then multiply by Avogadro to get 1/cm^3 (number density).
    const molPerVolume = this.density.div(this.bead_mass);
    const Na = Qty(6.022e23, "1/mol");
    const numberDensity = molPerVolume.mul(Na);
    return numberDensity;
  }

  public get n_chains_crosslinks(): number {
    if (this.stoichiometric_imbalance <= 0) return 0;
    return Math.trunc(
      ((this.n_bifunctional_chains * 2 + this.n_monofunctional_chains) *
        this.stoichiometric_imbalance) /
        this.crosslink_functionality
    );
  }

  public get total_n_beads_solvent(): number {
    return this.n_beads_zerofunctional * this.n_zerofunctional_chains;
  }

  public get total_n_beads_bifunctional(): number {
    return this.n_beads_bifunctional * this.n_bifunctional_chains;
  }

  public get total_n_beads_monofunctional(): number {
    return this.n_beads_monofunctional * this.n_monofunctional_chains;
  }

  public get total_n_beads_xlinks(): number {
    return this.n_beads_xlinks * this.n_chains_crosslinks;
  }

  public get n_beads_total(): number {
    return (
      this.total_n_beads_bifunctional +
      this.total_n_beads_monofunctional +
      this.total_n_beads_solvent +
      this.total_n_beads_xlinks
    );
  }

  public get n_chains_total(): number {
    return (
      this.n_bifunctional_chains +
      this.n_monofunctional_chains +
      this.n_zerofunctional_chains +
      this.n_chains_crosslinks
    );
  }

  is_mmtable(): boolean {
    return !(
      this.extract_solvent_before_measurement ||
      this.n_zerofunctional_chains > 0 ||
      this.n_beads_xlinks > 1
    );
  }

  // Helper to create from plain JSON (if needed)
  static fromJSON(json: any): PredictionInput {
    return new PredictionInput(json as PredictionInputInit);
  }

  public toSimpleObject(): object {
    const inputWithComputed = {
      ...this,
      b2: this.b2,
      n_beads_total: this.n_beads_total,
      n_chains_crosslinks: this.n_chains_crosslinks,
      mean_bead_distance: this.mean_bead_distance,
      bead_density: this.bead_density,
    };
    // Then, before returning, convert Qty objects to simple {value: , unit: } objects
    for (const key in inputWithComputed) {
      const value = inputWithComputed[key];
      if (value && value instanceof Qty) {
        inputWithComputed[key] = { value: value.scalar, unit: value.units() };
      }
    }
    return inputWithComputed;
  }
}
