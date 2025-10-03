import Qty from "js-quantities";

/**
 * Finds the best unit prefix for displaying the value in a human-readable range (1-1000).
 * Uses js-quantities to handle unit conversions properly.
 */
function findBestUnit(
  value: number,
  unit: string
): { value: number; unit: string } {
  try {
    const qty = new Qty(value, unit);

    // Extract the base unit by removing common SI prefixes
    const baseUnit = unit.replace(/^[nμmkMGT]/, "");

    // Try different SI prefixes to find the best scale
    const prefixes = [
      { symbol: "n", factor: 1e-9 },
      { symbol: "μ", factor: 1e-6 },
      { symbol: "m", factor: 1e-3 },
      { symbol: "", factor: 1 },
      { symbol: "k", factor: 1e3 },
      { symbol: "M", factor: 1e6 },
      { symbol: "G", factor: 1e9 },
      { symbol: "T", factor: 1e12 },
    ];

    // Try to find the best prefix where the scalar is between 1 and 1000
    for (const { symbol, factor } of prefixes) {
      try {
        const testUnit = symbol + baseUnit;
        const converted = qty.to(testUnit);
        const scalar = Math.abs(converted.scalar);

        // Use this unit if the value is in a good range
        if (scalar >= 1 && scalar < 1000) {
          return { value: converted.scalar, unit: testUnit };
        }
      } catch {
        // This prefix doesn't work for this unit type, try next
        continue;
      }
    }

    // If no good prefix found, return the original
    return { value, unit };
  } catch {
    // If js-quantities can't handle it, return unchanged
    return { value, unit };
  }
}

/**
 * Converts value and error to the best unit for display.
 */
function autoConvertUnit(
  value: number,
  error: number | undefined | null,
  unit: string | undefined | null
): { value: number; error: number; unit: string } {
  // If unit is missing, return with normalized types
  if (!unit) {
    return { value, error: error ?? 0, unit: "" };
  }

  try {
    // Find the best unit for the value (always convert, even without error)
    const { value: convertedValue, unit: bestUnit } = findBestUnit(value, unit);

    // Convert the error to the same unit if provided
    let convertedError = 0;
    if (error != null) {
      const errorQty = new Qty(error, unit);
      convertedError = errorQty.to(bestUnit).scalar;
    }

    return {
      value: convertedValue,
      error: convertedError,
      unit: bestUnit,
    };
  } catch {
    // Fallback to original if conversion fails
    return { value, error: error ?? 0, unit: unit ?? "" };
  }
}

/**
 * Gets the first significant digit of a number.
 */
function getFirstSignificantDigit(num: number): number {
  if (num === 0) return 0;
  const abs = Math.abs(num);
  const magnitude = Math.floor(Math.log10(abs));
  // Add small epsilon to handle floating point precision issues
  const firstDigit = Math.floor(abs / Math.pow(10, magnitude) + 1e-10);
  return firstDigit;
}

/**
 * Determines the number of decimal places to show based on the error.
 * Rule: Show 1 significant digit if first digit >= 3, otherwise 2 significant digits.
 * The first digit is determined after rounding to 1 significant digit.
 */
function getDecimalPlacesFromError(error: number, value: number): number {
  if (error === 0) {
    // No error: use reasonable default based on value magnitude
    const abs = Math.abs(value);
    if (abs === 0) return 2;
    const magnitude = Math.floor(Math.log10(abs));
    return Math.max(0, 2 - magnitude);
  }

  const errorMagnitude = Math.floor(Math.log10(Math.abs(error)));

  // Round error to 1 significant digit to see what the first digit will be
  const roundedTo1Sig =
    Math.round(error / Math.pow(10, errorMagnitude)) *
    Math.pow(10, errorMagnitude);
  const firstDigit = getFirstSignificantDigit(roundedTo1Sig);

  // If first digit >= 3, show 1 significant digit (round to error's magnitude)
  // If first digit < 3, show 2 significant digits (round to one place below error's magnitude)
  const decimalPlaces = firstDigit >= 3 ? -errorMagnitude : -errorMagnitude + 1;

  return Math.max(0, decimalPlaces);
}

/**
 * Rounds a number to the specified decimal places.
 * Keeps trailing zeros to maintain consistent precision display.
 */
function roundToDecimals(num: number, decimals: number): string {
  const factor = Math.pow(10, decimals);
  const rounded = Math.round(num * factor) / factor;
  return rounded.toFixed(decimals);
}

export function formatNumberWithErrorAndUnit(
  value: number,
  error: number | undefined | null,
  decimals: number | undefined | null,
  unit: string | undefined | null
): { value: string; error: string; unit: string } {
  // Step 1: Convert to best unit
  const {
    value: convertedValue,
    error: convertedError,
    unit: displayUnit,
  } = autoConvertUnit(value, error, unit);

  // Step 2: Determine precision
  const decimalPlaces =
    decimals !== null && decimals !== undefined
      ? decimals
      : getDecimalPlacesFromError(convertedError, convertedValue);

  // Step 3: Format the numbers
  const formattedValue = roundToDecimals(convertedValue, decimalPlaces);
  const formattedError =
    convertedError > 0 ? roundToDecimals(convertedError, decimalPlaces) : "";

  return {
    value: formattedValue,
    error: formattedError,
    unit: displayUnit,
  };
}
