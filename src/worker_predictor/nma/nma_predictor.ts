import type { PredictionInput } from "../../entity/PredictionInput";
import { DynamicModulusPredictorOutput } from "../../entity/PredictionOutput";
import { asyncRun } from "../../workerApi";
import pyScriptCode from "./worker_nma.py?raw";

export class NMAPredictor {
  async predict(
    input: PredictionInput
  ): Promise<DynamicModulusPredictorOutput> {
    let result = await asyncRun(pyScriptCode, {
      prediction_input: input.toSimpleObject(),
    });

    if (result.hasOwnProperty("result")) {
      return result.result;
    }
    if (result.hasOwnProperty("frequencies")) {
      let res = new DynamicModulusPredictorOutput();
      res.frequencies = result.frequencies;
      res.g_prime = result.g_prime;
      res.g_double_prime = result.g_double_prime;
      return res;
    }

    throw new Error(
      "Failed to predict NMA results",

      result.hasOwnProperty("error") ? result.error : result
    );
  }
}
