import { addQuantities, type Quantity } from "./Quantity";

export class ModulusPredictionOutput {
  phantom_modulus!: Quantity;
  entanglement_modulus!: Quantity;
  w_soluble!: Quantity;
  w_dangling!: Quantity;

  public get w_active() {
    return 1 - this.w_soluble.value - this.w_dangling.value;
  }

  public get modulus(): Quantity {
    return addQuantities(this.phantom_modulus, this.entanglement_modulus);
  }
}

export class DynamicModulusPredictorOutput {
  frequencies!: number[];
  g_prime!: number[];
  g_double_prime!: number[];
}
