// Lightweight quantity representation (value in given unit)
export interface Quantity {
  value: number;
  unit: string;
}

export function cloneQuantity(q: Quantity): Quantity {
  return { value: q.value, unit: q.unit };
}

export function divideQuantities(a: Quantity, b: Quantity, resultUnit: string): Quantity {
  return { value: a.value / b.value, unit: resultUnit };
}

export function multiplyQuantity(a: Quantity, factor: number): Quantity {
  return { value: a.value * factor, unit: a.unit };
}

export function addQuantities(a: Quantity, b: Quantity): Quantity {
  if (a.unit !== b.unit) {
    throw new Error(`Incompatible units: ${a.unit} and ${b.unit}`);
  }
  return { value: a.value + b.value, unit: a.unit };
}
