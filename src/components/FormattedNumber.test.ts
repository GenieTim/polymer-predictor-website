import { describe, it, expect } from "vitest";
import { formatNumberWithErrorAndUnit } from "../utils/FormattedNumber.utils";

describe("formatNumberWithErrorAndUnit", () => {
  it("formats value and error without unit, small numbers", () => {
    const result = formatNumberWithErrorAndUnit(0.001234, 0.000123, null, null);
    expect(result).toEqual({
      value: "0.00123",
      error: "0.00012",
      unit: "",
    });
  });

  it("formats value and error with unit, large error", () => {
    const result = formatNumberWithErrorAndUnit(12.34, 3.0, null, "MPa");
    expect(result).toEqual({
      value: "12",
      error: "3",
      unit: "MPa",
    });
  });

  it("auto-converts units for large values", () => {
    const result = formatNumberWithErrorAndUnit(5000, 191, null, "Pa");
    expect(result).toEqual({
      value: "5.00",
      error: "0.19",
      unit: "kPa",
    });
  });

  it("uses decimals if provided", () => {
    const result = formatNumberWithErrorAndUnit(1.2345, 0.1234, 3, "kg");
    expect(result).toEqual({
      value: "1.235", // Rounds to 3 decimals
      error: "0.123",
      unit: "kg",
    });
  });

  it("handles zero error with default precision", () => {
    const result = formatNumberWithErrorAndUnit(1.2345, 0, null, "kg");
    expect(result).toEqual({
      value: "1.23",
      error: "",
      unit: "kg",
    });
  });

  it("converts kg to g for small values", () => {
    const result = formatNumberWithErrorAndUnit(0.001, 0.0001, null, "kg");
    expect(result).toEqual({
      value: "1.00", // First digit of error (1) < 3, so 2 significant digits = 2 decimal places
      error: "0.10",
      unit: "g",
    });
  });

  it("handles very small errors (first digit < 3)", () => {
    const result = formatNumberWithErrorAndUnit(100.5, 0.2431, null, "Pa");
    expect(result).toEqual({
      value: "100.50",
      error: "0.24",
      unit: "Pa",
    });
  });

  it("handles very small errors (first digit > 3)", () => {
    const result = formatNumberWithErrorAndUnit(100.512, 0.2612, null, "Pa");
    expect(result).toEqual({
      value: "100.5",
      error: "0.3",
      unit: "Pa",
    });
  });

  it("handles medium errors (first digit >= 3)", () => {
    const result = formatNumberWithErrorAndUnit(100.0, 5.0, null, "Pa");
    expect(result).toEqual({
      value: "100",
      error: "5",
      unit: "Pa",
    });
  });

  it("converts to milliPascals for very small pressures", () => {
    const result = formatNumberWithErrorAndUnit(0.005, 0.0003, null, "Pa");
    expect(result).toEqual({
      value: "5.0",
      error: "0.3",
      unit: "mPa",
    });
  });

  it("handles large values in GPa", () => {
    const result = formatNumberWithErrorAndUnit(
      1500000000,
      50000000,
      null,
      "Pa"
    );
    expect(result).toEqual({
      value: "1.50",
      error: "0.05",
      unit: "GPa",
    });
  });

  it("respects explicit decimal override", () => {
    const result = formatNumberWithErrorAndUnit(123.456, 7.89, 1, "MPa");
    expect(result).toEqual({
      value: "123.5",
      error: "7.9",
      unit: "MPa",
    });
  });

  it("handles errors with first digit = 1", () => {
    const result = formatNumberWithErrorAndUnit(50.0, 1.5, null, "kg");
    expect(result).toEqual({
      value: "50.0",
      error: "1.5",
      unit: "kg",
    });
  });

  it("handles errors with first digit = 2", () => {
    const result = formatNumberWithErrorAndUnit(50.0, 2.4, null, "kg");
    expect(result).toEqual({
      value: "50.0",
      error: "2.4",
      unit: "kg",
    });
  });

  it("handles unitless values with appropriate precision", () => {
    const result = formatNumberWithErrorAndUnit(0.123, 0.045, null, null);
    expect(result).toEqual({
      value: "0.12",
      error: "0.05",
      unit: "",
    });
  });

  it("auto-converts units even without error (consistent with ANT)", () => {
    // This test verifies that unit conversion happens regardless of whether
    // an error is provided, ensuring consistency across all predictors
    const result = formatNumberWithErrorAndUnit(5000, undefined, null, "Pa");
    expect(result).toEqual({
      value: "5.00",
      error: "",
      unit: "kPa",
    });
  });

  it("auto-converts units with null error (consistent with ANT)", () => {
    const result = formatNumberWithErrorAndUnit(0.001, null, null, "MPa");
    expect(result).toEqual({
      value: "1.00",
      error: "",
      unit: "kPa",
    });
  });
});
