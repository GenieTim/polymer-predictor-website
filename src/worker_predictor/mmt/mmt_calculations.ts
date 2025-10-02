/**
 * Miller-Macosko Theory (MMT) calculations in TypeScript
 * 
 * This module provides various computations introduced in the Miller-Macosko theory.
 * Translated from pylimer_tools.calc.miller_macosko_theory
 * 
 * References:
 * - Miller & Macosko (1976)
 * - Langley (1968)
 * - Gusev (2022)
 * - Aoyama (2021)
 * 
 * Note: Currently supports only A_f and B_2 systems that are end-linked and monodisperse.
 */

import Qty from "js-quantities";

/**
 * Boltzmann constant in SI units (J/K)
 */
const KB = 1.380649e-23;

/**
 * Compute Macosko and Miller's probabilities P(F_A) and P(F_B)
 * i.e., the probability that a randomly chosen A (crosslink) or B (strand-end),
 * respectively, is the start of a finite chain.
 * 
 * @param r The stoichiometric imbalance
 * @param p The extent of reaction in terms of the crosslinkers
 * @param f The functionality of the crosslinker
 * @param b2 The fraction of bifunctional chains; defaults to 1.0 for no monofunctional chains
 * @returns [alpha, beta] where alpha is P(F_A) and beta is P(F_B)
 */
export function computeMillerMacoskoProbabilities(
  r: number,
  p: number,
  f: number,
  b2: number = 1.0
): [number, number] {
  if (r === 0 || p === 0 || f === 0) {
    return [0, 0];
  }
  if (b2 > 1 || b2 <= 0) {
    throw new Error(`b2 must be in (0, 1], got ${b2}`);
  }

  // Validate r and p
  validateRAndP(r, p, f);

  if (!(1 / (f - 1) < b2 * (p ** 2) * r && b2 * (p ** 2) * r < 1)) {
    throw new Error(
      `Invalid parameters: 1/(f-1) < b2*p^2*r < 1 must hold. Got: ${1/(f-1)} < ${b2 * (p**2) * r} < 1`
    );
  }

  let alpha: number;
  if (f === 3) {
    alpha = (1 - r * p * p * b2) / (r * p * p * b2);
  } else if (f === 4) {
    alpha = Math.sqrt((1.0 / (r * p * p * b2)) - 3.0 / 4.0) - (1.0 / 2.0);
  } else {
    throw new Error(`Functionality f=${f} not supported yet. Only f=3 and f=4 are implemented.`);
  }

  const beta = r * p * (alpha ** (f - 1)) + 1 - r * p;

  if (alpha > 1 || alpha < 0) {
    throw new Error(`alpha = ${alpha} is outside [0,1]. Check your parameters.`);
  }
  if (beta > 1 || beta < 0) {
    throw new Error(`beta = ${beta} is outside [0,1]. Check your parameters.`);
  }

  return [alpha, beta];
}

/**
 * Compute the Langley trapping factor T_e
 * 
 * @param beta P(F_B^out)
 * @returns The Langley trapping factor
 */
export function computeTrappingFactor(beta: number): number {
  // for long B2s reacting with small A_fs
  return (1 - beta) ** 4;
}

/**
 * Compute the probability that an A_f monomer will be an effective crosslink of exactly degree m
 * 
 * P(X_m^f) = C(f,m) * [P(F_A^out)]^(f-m) * [1-P(F_A^out)]^m
 * 
 * @param f functionality of monomer
 * @param m expected degree of effect
 * @param alpha P(F_A^out)
 * @returns The probability
 */
export function computeProbabilityEffectiveCrosslink(
  f: number,
  m: number,
  alpha: number
): number {
  if (alpha < 0 || alpha > 1) {
    throw new Error("alpha must be between 0 and 1");
  }
  return binomialCoefficient(f, m) * (alpha ** (f - m)) * ((1 - alpha) ** m);
}

/**
 * Compute the probability that a bifunctional monomer is effective
 * 
 * @param beta P(F_B^out)
 * @returns The probability
 */
export function computeProbabilityEffectiveBifunctional(beta: number): number {
  if (beta < 0 || beta > 1) {
    throw new Error("beta must be between 0 and 1");
  }
  return (1 - beta) ** 2;
}

/**
 * Compute the probability that a crosslink is dangling (pendant)
 * This is equal to the probability that only one of the arms is attached to the gel.
 * 
 * @param f functionality of monomer
 * @param alpha P(F_A^out)
 * @returns The probability
 */
export function computeProbabilityDanglingCrosslink(f: number, alpha: number): number {
  if (alpha < 0 || alpha > 1) {
    throw new Error("alpha must be between 0 and 1");
  }
  return binomialCoefficient(f, 1) * (alpha ** (f - 1)) * (1 - alpha);
}

/**
 * Compute the probability that a bifunctional monomer is dangling
 * 
 * @param beta P(F_B^out)
 * @returns The probability
 */
export function computeProbabilityDanglingBifunctional(beta: number): number {
  if (beta < 0 || beta > 1) {
    throw new Error("beta must be between 0 and 1");
  }
  return 2 * beta * (1 - beta);
}

/**
 * Compute the weight fraction of dangling (pendant) strands in infinite network
 * 
 * @param functionalityPerType Dictionary with key: type, value: functionality
 * @param weightFractions Dictionary with weight fraction of each type
 * @param alpha P(F_A^out)
 * @param beta P(F_B^out)
 * @returns Weight fraction of dangling chains
 */
export function computeWeightFractionDanglingChains(
  functionalityPerType: Record<number, number>,
  weightFractions: Record<number, number>,
  alpha: number,
  beta: number
): number {
  let wDangling = 0.0;

  for (const [atomType, weightFraction] of Object.entries(weightFractions)) {
    const type = Number(atomType);
    const functionality = functionalityPerType[type];

    if (functionality === 1) {
      // Monofunctional chains are always dangling
      wDangling += weightFraction;
    } else if (functionality === 2) {
      // Bifunctional chains
      wDangling += weightFraction * computeProbabilityDanglingBifunctional(beta);
    } else if (functionality >= 3) {
      // Crosslinkers
      wDangling += weightFraction * computeProbabilityDanglingCrosslink(functionality, alpha);
    }
  }

  return wDangling;
}

/**
 * Compute the weight fraction of the backbone (elastically effective) strands
 * 
 * @param functionalityPerType Dictionary with key: type, value: functionality
 * @param weightFractions Dictionary with weight fraction of each type
 * @param alpha P(F_A^out)
 * @param beta P(F_B^out)
 * @returns Weight fraction of backbone
 */
export function computeWeightFractionBackbone(
  functionalityPerType: Record<number, number>,
  weightFractions: Record<number, number>,
  alpha: number,
  beta: number
): number {
  let wElastic = 0.0;

  for (const [atomType, weightFraction] of Object.entries(weightFractions)) {
    const type = Number(atomType);
    const functionality = functionalityPerType[type];

    if (functionality === 1) {
      // Monofunctional chains are not elastic
      continue;
    } else if (functionality === 2) {
      // Bifunctional chains
      wElastic += weightFraction * computeProbabilityEffectiveBifunctional(beta);
    } else if (functionality >= 3) {
      // Crosslinkers - sum over all effective degrees
      for (let m = 2; m <= functionality; m++) {
        wElastic += weightFraction * computeProbabilityEffectiveCrosslink(functionality, m, alpha);
      }
    }
  }

  return wElastic;
}

/**
 * Compute the weight fraction of soluble material by MMT
 * 
 * @param functionalityPerType Dictionary with key: type, value: functionality
 * @param weightFractions Dictionary with weight fraction of each type
 * @param alpha P(F_A^out)
 * @param beta P(F_B^out)
 * @returns Weight fraction of soluble material
 */
export function computeWeightFractionSolubleMaterial(
  functionalityPerType: Record<number, number>,
  weightFractions: Record<number, number>,
  alpha: number,
  beta: number
): number {
  let wSol = 0;

  for (const [atomType, weightFraction] of Object.entries(weightFractions)) {
    const type = Number(atomType);
    const functionality = functionalityPerType[type];

    if (functionality === 2) {
      // Bifunctional chains
      wSol += weightFraction * (beta ** 2);
    } else if (functionality >= 3) {
      // Crosslinkers
      wSol += weightFraction * (alpha ** functionality);
    } else {
      // Monofunctional or zerofunctional
      wSol += weightFraction;
    }
  }

  return wSol;
}

/**
 * Compute MMT's junction modulus
 * 
 * G_junctions = k_B T [A_f]_0 * sum_{m=3}^{f} (m-2)/2 * P(X_{m,f})
 * 
 * @param p The crosslinker conversion
 * @param r The stoichiometric imbalance
 * @param xlinkConcentration0 [A_f]_0 in 1/volume units (as Qty)
 * @param f The functionality of the crosslinkers
 * @param temperature The temperature (as Qty)
 * @param b2 The fraction of bifunctional chains
 * @returns The junction modulus (as Qty)
 */
export function computeJunctionModulus(
  p: number,
  r: number,
  xlinkConcentration0: Qty,
  f: number,
  temperature: Qty,
  b2: number = 1.0
): Qty {
  const [alpha, _] = computeMillerMacoskoProbabilities(r, p, f, b2);
  
  let gammaMmtSum = 0.0;
  for (let m = 3; m <= f; m++) {
    const prob = computeProbabilityEffectiveCrosslink(f, m, alpha);
    gammaMmtSum += ((m - 2) / 2) * prob;
  }

  // Convert temperature to Kelvin
  const T = temperature.to("tempK").scalar;
  // Convert concentration to 1/m^3
  const conc = xlinkConcentration0.to("1/m^3").scalar;
  
  // G = k_B * T * concentration * gamma_sum
  // Result in Pa (J/m^3)
  const gPa = KB * T * conc * gammaMmtSum;
  
  return Qty(gPa, "Pa");
}

/**
 * Compute MMT's entanglement contribution to the equilibrium shear modulus
 * 
 * @param ge1 The melt entanglement modulus G_e(1) = k_B T * epsilon_e
 * @param beta P(F_B^out)
 * @returns T_e * G_e(1) (as Qty)
 */
export function computeEntanglementModulus(
  ge1: Qty,
  beta: number
): Qty {
  const trappingFactor = computeTrappingFactor(beta);
  return ge1.mul(trappingFactor);
}

/**
 * Compute four different estimates of the plateau modulus using MMT, ANM and PNM
 * 
 * @param r The stoichiometric imbalance
 * @param p The extent of reaction
 * @param f The functionality of the crosslinker
 * @param nu The strand number density (nr of strands per volume) (as Qty)
 * @param temperature The temperature (as Qty)
 * @param ge1 The melt entanglement modulus (as Qty)
 * @param b2 The fraction of bifunctional chains
 * @returns [G_MMT_phantom, G_MMT_entanglement, G_ANM, G_PNM] all as Qty
 */
export function computeModulusDecomposition(
  r: number,
  p: number,
  f: number,
  nu: Qty,
  temperature: Qty,
  ge1: Qty,
  b2: number = 1.0
): [Qty, Qty, Qty, Qty] {
  const [alpha, beta] = computeMillerMacoskoProbabilities(r, p, f, b2);
  
  // Convert to SI units
  const T = temperature.to("tempK").scalar;
  const nuVal = nu.to("1/m3").scalar;
  
  // k_B * T * nu
  const kbTNu = KB * T * nuVal;
  
  // ANM (affine)
  const gAnm = Qty(kbTNu, "Pa");
  
  // PNM (phantom)
  const gPnm = Qty((1 - 2 / f) * kbTNu, "Pa");
  
  // MMT phantom part
  let gammaMmtSum = 0.0;
  for (let m = 3; m <= f; m++) {
    const prob = computeProbabilityEffectiveCrosslink(f, m, alpha);
    gammaMmtSum += ((m - 2) / 2) * prob;
  }
  const gammaMmt = (2 * r * b2 / f) * gammaMmtSum;
  const gMmtPhantom = Qty(gammaMmt * kbTNu, "Pa");
  
  // MMT entanglement part
  const gMmtEntanglement = computeEntanglementModulus(ge1, beta);
  
  return [gMmtPhantom, gMmtEntanglement, gAnm, gPnm];
}

/**
 * Predict the shear modulus using MMT Analysis
 * 
 * @param r The stoichiometric imbalance
 * @param p The extent of reaction
 * @param f The functionality of the crosslinker
 * @param nu The strand number density (as Qty)
 * @param temperature The temperature (as Qty)
 * @param ge1 The melt entanglement modulus (as Qty)
 * @param b2 The fraction of bifunctional chains
 * @returns G: The predicted shear modulus (as Qty)
 */
export function predictShearModulus(
  r: number,
  p: number,
  f: number,
  nu: Qty,
  temperature: Qty,
  ge1: Qty,
  b2: number = 1.0
): Qty {
  const [gMmtPhantom, gMmtEntanglement, _, __] = computeModulusDecomposition(
    r, p, f, nu, temperature, ge1, b2
  );
  return gMmtPhantom.add(gMmtEntanglement);
}

// ============================================================================
// Helper functions
// ============================================================================

/**
 * Binomial coefficient C(n, k) = n! / (k! * (n-k)!)
 */
function binomialCoefficient(n: number, k: number): number {
  if (k < 0 || k > n) return 0;
  if (k === 0 || k === n) return 1;
  
  let result = 1;
  for (let i = 1; i <= k; i++) {
    result *= (n - i + 1) / i;
  }
  return result;
}

/**
 * Validate r and p parameters
 */
function validateRAndP(r: number, p: number, f: number): void {
  if (r <= 0) {
    throw new Error(`Stoichiometric imbalance r must be positive, got ${r}`);
  }
  if (p < 0 || p > 1) {
    throw new Error(`Conversion p must be in [0,1], got ${p}`);
  }
  if (!Number.isFinite(r) || !Number.isFinite(p)) {
    throw new Error("r and p must be finite numbers");
  }
  if (f < 2) {
    throw new Error(`Functionality f must be >= 2, got ${f}`);
  }
}
