import Qty from "js-quantities";

export class ModulusPredictionOutput {
  phantom_modulus!: Qty;
  entanglement_modulus!: Qty;
  w_soluble!: Qty;
  w_dangling!: Qty;

  public get w_active(): Qty {
    return Qty(1, "").sub(this.w_soluble).sub(this.w_dangling);
  }

  public get modulus(): Qty {
    return this.phantom_modulus.add(this.entanglement_modulus);
  }
}

export class DynamicModulusPredictorOutput {
  frequencies!: number[];
  g_prime!: number[];
  g_double_prime!: number[];
}
