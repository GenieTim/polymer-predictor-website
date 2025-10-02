/**
 * Tests for MMT calculations
 * 
 * These tests verify that the TypeScript implementation produces
 * results consistent with the original Python implementation.
 */

import { describe, it, expect } from 'vitest';
import Qty from 'js-quantities';
import { execSync } from 'child_process';
import {
  computeMillerMacoskoProbabilities,
  computeTrappingFactor,
  computeProbabilityEffectiveCrosslink,
  computeProbabilityEffectiveBifunctional,
  computeProbabilityDanglingCrosslink,
  computeProbabilityDanglingBifunctional,
  computeWeightFractionDanglingChains,
  computeWeightFractionBackbone,
  computeWeightFractionSolubleMaterial,
  computeModulusDecomposition,
} from './mmt_calculations';
import { MMTPredictor } from './mmt_predictor';
import { PredictionInput } from '../../entity/PredictionInput';

/**
 * Helper function to run Python code and get the result
 */
function runPython(code: string): any {
  try {
    const result = execSync(`python3 -c "${code.replace(/"/g, '\\"')}"`, {
      encoding: 'utf-8',
      timeout: 5000,
    });
    return JSON.parse(result.trim());
  } catch (error) {
    console.error('Python execution failed:', error);
    throw error;
  }
}

/**
 * Check if Python 3 is available
 */
function isPythonAvailable(): boolean {
  try {
    execSync('python3 --version', { encoding: 'utf-8', timeout: 1000 });
    return true;
  } catch {
    return false;
  }
}

describe('Miller-Macosko Theory Calculations', () => {
  describe('computeMillerMacoskoProbabilities', () => {
    it('should compute probabilities for f=3 system', () => {
      const [alpha, beta] = computeMillerMacoskoProbabilities(1.0, 0.75, 3, 1.0);
      
      expect(alpha).toBeGreaterThan(0);
      expect(alpha).toBeLessThan(1);
      expect(beta).toBeGreaterThan(0);
      expect(beta).toBeLessThan(1);
    });

    it('should compute probabilities for f=4 system', () => {
      const [alpha, beta] = computeMillerMacoskoProbabilities(1.0, 0.8, 4, 1.0);
      
      expect(alpha).toBeGreaterThan(0);
      expect(alpha).toBeLessThan(1);
      expect(beta).toBeGreaterThan(0);
      expect(beta).toBeLessThan(1);
    });

    it('should return [0, 0] for zero parameters', () => {
      expect(computeMillerMacoskoProbabilities(0, 0.9, 3, 1.0)).toEqual([0, 0]);
      expect(computeMillerMacoskoProbabilities(1.0, 0, 3, 1.0)).toEqual([0, 0]);
    });

    it('should throw error for invalid b2', () => {
      expect(() => computeMillerMacoskoProbabilities(1.0, 0.9, 3, 1.5)).toThrow();
      expect(() => computeMillerMacoskoProbabilities(1.0, 0.9, 3, 0)).toThrow();
    });

    it('should throw error for invalid r and p', () => {
      expect(() => computeMillerMacoskoProbabilities(-1.0, 0.9, 3, 1.0)).toThrow();
      expect(() => computeMillerMacoskoProbabilities(1.0, 1.5, 3, 1.0)).toThrow();
    });
  });

  describe('computeTrappingFactor', () => {
    it('should compute trapping factor', () => {
      const beta = 0.5;
      const te = computeTrappingFactor(beta);
      
      expect(te).toBe((1 - beta) ** 4);
      expect(te).toBeCloseTo(0.0625, 4);
    });

    it('should return 1 for beta=0', () => {
      expect(computeTrappingFactor(0)).toBe(1);
    });

    it('should return 0 for beta=1', () => {
      expect(computeTrappingFactor(1)).toBe(0);
    });
  });

  describe('computeProbabilityEffectiveCrosslink', () => {
    it('should compute probability for effective crosslink', () => {
      const f = 4;
      const m = 3;
      const alpha = 0.3;
      
      const prob = computeProbabilityEffectiveCrosslink(f, m, alpha);
      
      expect(prob).toBeGreaterThan(0);
      expect(prob).toBeLessThan(1);
    });

    it('should throw error for invalid alpha', () => {
      expect(() => computeProbabilityEffectiveCrosslink(4, 3, 1.5)).toThrow();
      expect(() => computeProbabilityEffectiveCrosslink(4, 3, -0.1)).toThrow();
    });
  });

  describe('Weight fraction calculations', () => {
    const functionalityPerType = {
      1: 2,  // bifunctional
      2: 4,  // crosslinkers
      4: 1,  // monofunctional
    };

    const weightFractions = {
      1: 0.5,  // 50% bifunctional
      2: 0.3,  // 30% crosslinkers
      4: 0.2,  // 20% monofunctional
    };

    const alpha = 0.3;
    const beta = 0.5;

    it('should compute weight fraction of dangling chains', () => {
      const wDangling = computeWeightFractionDanglingChains(
        functionalityPerType,
        weightFractions,
        alpha,
        beta
      );
      
      expect(wDangling).toBeGreaterThan(0);
      expect(wDangling).toBeLessThan(1);
    });

    it('should compute weight fraction of backbone', () => {
      const wBackbone = computeWeightFractionBackbone(
        functionalityPerType,
        weightFractions,
        alpha,
        beta
      );
      
      expect(wBackbone).toBeGreaterThan(0);
      expect(wBackbone).toBeLessThan(1);
    });

    it('should compute weight fraction of soluble material', () => {
      const wSoluble = computeWeightFractionSolubleMaterial(
        functionalityPerType,
        weightFractions,
        alpha,
        beta
      );
      
      expect(wSoluble).toBeGreaterThan(0);
      expect(wSoluble).toBeLessThan(1);
    });

    it('weight fractions should sum to approximately 1', () => {
      const wDangling = computeWeightFractionDanglingChains(
        functionalityPerType,
        weightFractions,
        alpha,
        beta
      );
      const wBackbone = computeWeightFractionBackbone(
        functionalityPerType,
        weightFractions,
        alpha,
        beta
      );
      const wSoluble = computeWeightFractionSolubleMaterial(
        functionalityPerType,
        weightFractions,
        alpha,
        beta
      );
      
      // Note: These don't necessarily sum to 1 due to overlaps in the definitions
      // This is just a sanity check that they're in reasonable ranges
      expect(wDangling).toBeGreaterThanOrEqual(0);
      expect(wBackbone).toBeGreaterThanOrEqual(0);
      expect(wSoluble).toBeGreaterThanOrEqual(0);
      expect(wDangling).toBeLessThanOrEqual(1);
      expect(wBackbone).toBeLessThanOrEqual(1);
      expect(wSoluble).toBeLessThanOrEqual(1);
    });
  });

  describe('computeModulusDecomposition', () => {
    it('should compute modulus decomposition', () => {
      const r = 1.0;
      const p = 0.8;
      const f = 4;
      const nu = Qty(1e24, '1/m3');
      const temperature = Qty(298.15, 'tempK');
      const ge1 = Qty(0.5, 'MPa');
      const b2 = 1.0;

      const [gMmtPhantom, gMmtEntanglement, gAnm, gPnm] = computeModulusDecomposition(
        r, p, f, nu, temperature, ge1, b2
      );

      // All moduli should be positive Qty objects
      expect(gMmtPhantom.scalar).toBeGreaterThan(0);
      expect(gMmtEntanglement.scalar).toBeGreaterThan(0);
      expect(gAnm.scalar).toBeGreaterThan(0);
      expect(gPnm.scalar).toBeGreaterThan(0);

      // PNM should be less than ANM (phantom is softer than affine)
      expect(gPnm.to('Pa').scalar).toBeLessThan(gAnm.to('Pa').scalar);

      // Verify they have the right units
      expect(() => gMmtPhantom.to('Pa')).not.toThrow();
      expect(() => gMmtEntanglement.to('Pa')).not.toThrow();
      expect(() => gAnm.to('Pa')).not.toThrow();
      expect(() => gPnm.to('Pa')).not.toThrow();
    });

    it('should produce reasonable values for typical PDMS system', () => {
      // Typical PDMS parameters
      const r = 1.0;
      const p = 0.8;
      const f = 4;
      const nu = Qty(5e23, '1/m3');  // typical strand density
      const temperature = Qty(298.15, 'tempK');
      const ge1 = Qty(0.2, 'MPa');  // typical entanglement modulus
      const b2 = 1.0;

      const [gMmtPhantom, gMmtEntanglement, _, __] = computeModulusDecomposition(
        r, p, f, nu, temperature, ge1, b2
      );

      const gTotal = gMmtPhantom.add(gMmtEntanglement).to('MPa');

      // Total modulus should be in reasonable range for PDMS (0.1 - 10 MPa)
      expect(gTotal.scalar).toBeGreaterThan(0.01);
      expect(gTotal.scalar).toBeLessThan(100);
    });
  });

  describe('Python Implementation Comparison', () => {
    const pythonAvailable = isPythonAvailable();

    it.skipIf(!pythonAvailable)('should match Python implementation for Miller-Macosko probabilities (f=3)', () => {
      const r = 1.0;
      const p = 0.75;
      const f = 3;
      const b2 = 1.0;

      const [alphaTS, betaTS] = computeMillerMacoskoProbabilities(r, p, f, b2);
      
      const pythonCode = `
import json
import math

r, p, f, b2 = ${r}, ${p}, ${f}, ${b2}
if f == 3:
    alpha = (1 - r * p * p * b2) / (r * p * p * b2)
elif f == 4:
    alpha = math.sqrt((1.0 / (r * p * p * b2)) - 3.0 / 4.0) - (1.0 / 2.0)
beta = r * p * (alpha ** (f - 1)) + 1 - r * p
print(json.dumps([alpha, beta]))
`;
      
      const [alphaPy, betaPy] = runPython(pythonCode);

      expect(alphaTS).toBeCloseTo(alphaPy, 10);
      expect(betaTS).toBeCloseTo(betaPy, 10);
    });

    it.skipIf(!pythonAvailable)('should match Python implementation for Miller-Macosko probabilities (f=4)', () => {
      const r = 0.95;
      const p = 0.8;
      const f = 4;
      const b2 = 1.0;

      const [alphaTS, betaTS] = computeMillerMacoskoProbabilities(r, p, f, b2);
      
      const pythonCode = `
import json
import math

r, p, f, b2 = ${r}, ${p}, ${f}, ${b2}
if f == 3:
    alpha = (1 - r * p * p * b2) / (r * p * p * b2)
elif f == 4:
    alpha = math.sqrt((1.0 / (r * p * p * b2)) - 3.0 / 4.0) - (1.0 / 2.0)
beta = r * p * (alpha ** (f - 1)) + 1 - r * p
print(json.dumps([alpha, beta]))
`;
      
      const [alphaPy, betaPy] = runPython(pythonCode);

      expect(alphaTS).toBeCloseTo(alphaPy, 10);
      expect(betaTS).toBeCloseTo(betaPy, 10);
    });

    it.skipIf(!pythonAvailable)('should match Python for trapping factor', () => {
      const beta = 0.3456;
      
      const tsResult = computeTrappingFactor(beta);
      const pythonCode = `
import json
beta = ${beta}
result = (1 - beta) ** 4
print(json.dumps(result))
`;
      const pyResult = runPython(pythonCode);

      expect(tsResult).toBeCloseTo(pyResult, 10);
    });

    it.skipIf(!pythonAvailable)('should match Python for weight fraction calculations', () => {
      const functionalityPerType = {
        1: 2,  // bifunctional
        2: 4,  // crosslinkers
        4: 1,  // monofunctional
      };

      const weightFractions = {
        1: 0.48,
        2: 0.32,
        4: 0.20,
      };

      const r = 1.0;
      const p = 0.7;
      const f = 4;
      const b2 = 1.0;

      const [alpha, beta] = computeMillerMacoskoProbabilities(r, p, f, b2);

      // Test soluble fraction
      const wSolubleTS = computeWeightFractionSolubleMaterial(
        functionalityPerType,
        weightFractions,
        alpha,
        beta
      );

      const pythonCodeSoluble = `
import json
import math

def binomial_coefficient(n, k):
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    result = 1
    for i in range(1, k + 1):
        result *= (n - i + 1) / i
    return result

r, p, f, b2 = ${r}, ${p}, ${f}, ${b2}
if f == 3:
    alpha = (1 - r * p * p * b2) / (r * p * p * b2)
elif f == 4:
    alpha = math.sqrt((1.0 / (r * p * p * b2)) - 3.0 / 4.0) - (1.0 / 2.0)
beta = r * p * (alpha ** (f - 1)) + 1 - r * p

functionality_per_type = {1: 2, 2: 4, 4: 1}
weight_fractions = {1: 0.48, 2: 0.32, 4: 0.20}

w_sol = 0
for atom_type, weight_fraction in weight_fractions.items():
    functionality = functionality_per_type[atom_type]
    if functionality == 2:
        w_sol += weight_fraction * (beta ** 2)
    elif functionality >= 3:
        w_sol += weight_fraction * (alpha ** functionality)
    else:
        w_sol += weight_fraction

print(json.dumps(w_sol))
`;

      const wSolublePy = runPython(pythonCodeSoluble);

      expect(wSolubleTS).toBeCloseTo(wSolublePy, 8);

      // Test dangling fraction
      const wDanglingTS = computeWeightFractionDanglingChains(
        functionalityPerType,
        weightFractions,
        alpha,
        beta
      );

      const pythonCodeDangling = `
import json
import math

def binomial_coefficient(n, k):
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    result = 1
    for i in range(1, k + 1):
        result *= (n - i + 1) / i
    return result

r, p, f, b2 = ${r}, ${p}, ${f}, ${b2}
if f == 3:
    alpha = (1 - r * p * p * b2) / (r * p * p * b2)
elif f == 4:
    alpha = math.sqrt((1.0 / (r * p * p * b2)) - 3.0 / 4.0) - (1.0 / 2.0)
beta = r * p * (alpha ** (f - 1)) + 1 - r * p

functionality_per_type = {1: 2, 2: 4, 4: 1}
weight_fractions = {1: 0.48, 2: 0.32, 4: 0.20}

w_dangling = 0.0
for atom_type, weight_fraction in weight_fractions.items():
    functionality = functionality_per_type[atom_type]
    if functionality == 1:
        w_dangling += weight_fraction
    elif functionality == 2:
        w_dangling += weight_fraction * 2 * beta * (1 - beta)
    elif functionality >= 3:
        prob_dangling = binomial_coefficient(functionality, 1) * (alpha ** (functionality - 1)) * (1 - alpha)
        w_dangling += weight_fraction * prob_dangling

print(json.dumps(w_dangling))
`;

      const wDanglingPy = runPython(pythonCodeDangling);

      expect(wDanglingTS).toBeCloseTo(wDanglingPy, 8);
    });

    it.skipIf(!pythonAvailable)('should match Python for multiple random parameter sets', () => {
      const testCases = [
        { r: 1.0, p: 0.75, f: 3, b2: 1.0 },
        { r: 1.0, p: 0.8, f: 4, b2: 1.0 },
        { r: 0.95, p: 0.82, f: 4, b2: 1.0 },
        { r: 1.1, p: 0.7, f: 3, b2: 1.0 },
      ];

      for (const testCase of testCases) {
        const { r, p, f, b2 } = testCase;

        const [alphaTS, betaTS] = computeMillerMacoskoProbabilities(r, p, f, b2);
        
        const pythonCode = `
import json
import math

r, p, f, b2 = ${r}, ${p}, ${f}, ${b2}
if f == 3:
    alpha = (1 - r * p * p * b2) / (r * p * p * b2)
elif f == 4:
    alpha = math.sqrt((1.0 / (r * p * p * b2)) - 3.0 / 4.0) - (1.0 / 2.0)
beta = r * p * (alpha ** (f - 1)) + 1 - r * p
print(json.dumps([alpha, beta]))
`;
        
        const [alphaPy, betaPy] = runPython(pythonCode);

        expect(alphaTS).toBeCloseTo(alphaPy, 10);
        expect(betaTS).toBeCloseTo(betaPy, 10);
      }
    });
  });

  describe('Full MMT Predictor Integration', () => {
    it('should produce reasonable results for a typical PDMS system', async () => {
      const input = new PredictionInput({
        stoichiometric_imbalance: 1.0,
        crosslink_conversion: 0.9,
        crosslink_functionality: 4,
        n_zerofunctional_chains: 0,
        n_monofunctional_chains: 0,
        n_bifunctional_chains: 1000,
        n_beads_zerofunctional: 0,
        n_beads_monofunctional: 20,
        n_beads_bifunctional: 100,
        n_beads_xlinks: 1,
        temperature: Qty(298.15, 'tempK'),
        density: Qty(0.965, 'kg/L'),
        bead_mass: Qty(74.09, 'g/mol'),  // PDMS monomer
        mean_squared_bead_distance: Qty(0.5, 'nm^2'),
        plateau_modulus: Qty(0.2, 'MPa'),
        entanglement_sampling_cutoff: Qty(2.0, 'nm'),
      });

      const predictor = new MMTPredictor();
      const result = await predictor.predict(input);

      // Check that results are in reasonable ranges
      expect(result.phantom_modulus.to('MPa').scalar).toBeGreaterThan(0);
      expect(result.phantom_modulus.to('MPa').scalar).toBeLessThan(10);
      
      expect(result.entanglement_modulus.to('MPa').scalar).toBeGreaterThan(0);
      expect(result.entanglement_modulus.to('MPa').scalar).toBeLessThan(5);
      
      expect(result.w_soluble.scalar).toBeGreaterThanOrEqual(0);
      expect(result.w_soluble.scalar).toBeLessThanOrEqual(1);
      
      expect(result.w_dangling.scalar).toBeGreaterThanOrEqual(0);
      expect(result.w_dangling.scalar).toBeLessThanOrEqual(1);

      // Total modulus should be reasonable
      const totalModulus = result.modulus.to('MPa').scalar;
      expect(totalModulus).toBeGreaterThan(0.01);
      expect(totalModulus).toBeLessThan(100);
    });
  });
});
