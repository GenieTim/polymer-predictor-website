import type { PredictionInput } from "../../entity/PredictionInput";
import { ModulusPredictionOutput } from "../../entity/PredictionOutput";
import type { Predictor } from "../predictor";
import { asyncRun } from "../../workerApi";
import pyScriptCode from "./worker_mmt.py?raw";
import Qty from "js-quantities";

export class MMTPredictor implements Predictor {
  async predict(input: PredictionInput): Promise<ModulusPredictionOutput> {
    console.log("Predicting MMT results...", input.toSimpleObject());
    let result = await asyncRun(pyScriptCode, {
      prediction_input: input.toSimpleObject(),
    });
    if (result.hasOwnProperty("result")) {
      result = result.result;
    }
    // if the result already has all fields of type ModulusPredictionOutput
    if (result.hasOwnProperty("phantom_modulus") && result.hasOwnProperty("entanglement_modulus")) {
      // we still need to parse the values to quantities
      let parsedResult= new ModulusPredictionOutput();
      parsedResult.phantom_modulus = Qty(result.phantom_modulus, "MPa");
      parsedResult.entanglement_modulus = Qty(result.entanglement_modulus, "MPa");
      parsedResult.w_soluble = Qty(result.w_soluble, "");
      parsedResult.w_dangling = Qty(result.w_dangling, "");
      return parsedResult;
    }

    throw new Error(
      "Failed to predict MMT results: " + (result.hasOwnProperty("error") ? result.error : JSON.stringify(result))
    );
  }
}
