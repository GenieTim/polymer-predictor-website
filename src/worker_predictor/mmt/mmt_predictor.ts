import type { PredictionInput } from "../../entity/PredictionInput";
import { ModulusPredictionOutput } from "../../entity/PredictionOutput";
import type { Predictor } from "../predictor";
import Qty from "js-quantities";
import {
  computeMillerMacoskoProbabilities,
  computeModulusDecomposition,
  computeWeightFractionDanglingChains,
  computeWeightFractionBackbone,
  computeWeightFractionSolubleMaterial,
} from "./mmt_calculations";

export class MMTPredictor implements Predictor {
  async predict(input: PredictionInput): Promise<ModulusPredictionOutput> {
    console.log("Predicting MMT results...", input);

    try {
      const result = this.predictMMTResults(input);
      return result;
    } catch (error) {
      throw new Error(
        `Failed to predict MMT results: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  private predictMMTResults(input: PredictionInput): ModulusPredictionOutput {
    const r = input.stoichiometric_imbalance;
    const p = input.crosslink_conversion;
    const f = input.crosslink_functionality;
    const ge1 = input.plateau_modulus;
    const temperature = input.temperature;
    const density = input.density;
    const b2 = input.b2;

    // Calculate molecular weights
    const Mw1 = input.bead_mass.mul(input.n_beads_monofunctional);
    const Mw2 = input.bead_mass.mul(input.n_beads_bifunctional);
    const MwX = input.bead_mass.mul(input.n_beads_xlinks);

    // Convert molecular weights from g/mol to kg (actual mass) using Avogadro's number
    const Na = Qty(6.022e23, "1/mol");
    const Mw1Kg = Mw1.div(Na).to("kg");
    const Mw2Kg = Mw2.div(Na).to("kg");
    const MwXKg = MwX.div(Na).to("kg");

    // Calculate number of chains
    const nChains = 1e7;
    const nChainsMono = Math.trunc((2 * nChains * (1 - b2)) / b2);

    // Calculate effective molecular weight
    const MwEff = Mw2Kg.mul(nChains)
      .add(Mw1Kg.mul(nChainsMono))
      .div(nChains + nChainsMono);

    // Calculate strand number density
    const nu = density.div(MwEff);

    // Compute modulus decomposition
    const [gMmtPhantom, gMmtEntanglement, gAnm, gPnm] = computeModulusDecomposition(
      r,
      p,
      f,
      nu,
      temperature,
      ge1,
      b2
    );

    // Calculate b2 entanglement correction
    const b2EntanglementCorrection = Mw2.mul(nChains)
      .div(Mw1.mul(nChainsMono).add(Mw2.mul(nChains)))
      .scalar;

    // Apply correction to entanglement modulus
    const correctedEntanglementModulus = gMmtEntanglement.mul(b2EntanglementCorrection);

    // Calculate weight fractions for MMT
    const nCrosslinks = Math.trunc(((nChains * 2 + nChainsMono) * r) / f);
    const totalWeight = Mw1.mul(nChainsMono)
      .add(Mw2.mul(nChains))
      .add(MwX.mul(nCrosslinks));

    const weightFractions: Record<number, number> = {
      1: Mw2.mul(nChains).div(totalWeight).scalar, // bifunctional
      2: MwX.mul(nCrosslinks).div(totalWeight).scalar, // crosslinkers
      4: Mw1.mul(nChainsMono).div(totalWeight).scalar, // monofunctional
    };

    const functionalityPerType: Record<number, number> = {
      1: 2, // bifunctional chains
      2: f, // crosslinkers
      4: 1, // monofunctional chains
    };

    // Compute probabilities
    const [alpha, beta] = computeMillerMacoskoProbabilities(r, p, f, b2);

    // Compute weight fractions
    const wSoluble = computeWeightFractionSolubleMaterial(
      functionalityPerType,
      weightFractions,
      alpha,
      beta
    );

    const wDangling = computeWeightFractionDanglingChains(
      functionalityPerType,
      weightFractions,
      alpha,
      beta
    );

    // Create output
    const output = new ModulusPredictionOutput();
    output.phantom_modulus = gMmtPhantom.to("MPa");
    output.entanglement_modulus = correctedEntanglementModulus.to("MPa");
    output.w_soluble = Qty(wSoluble, "");
    output.w_dangling = Qty(wDangling, "");

    return output;
  }
}
