/**
 * Shared utility functions for result components
 */

export function format2(v?: number): string {
  return v == null || !isFinite(v) ? "-" : v.toFixed(2);
}

export function myQtyFormatter(scalar: number, unit: string): string {
  return scalar == null || !isFinite(scalar)
    ? "-"
    : `${scalar.toFixed(2)} ${unit}`.trim();
}

export function mean(vals: number[]): number {
  return vals.reduce((a, b) => a + b, 0) / vals.length;
}

export function std(vals: number[]): number {
  if (vals.length < 2) return 0;
  const m = mean(vals);
  const v = vals.reduce((s, x) => s + (x - m) ** 2, 0) / (vals.length - 1);
  return Math.sqrt(v);
}
