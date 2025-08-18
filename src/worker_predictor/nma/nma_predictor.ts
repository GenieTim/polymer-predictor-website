import type { PredictionInput } from "../../entity/PredictionInput";
import type { DynamicModulusPredictorOutput } from "../../entity/PredictionOutput";
import { asyncRun } from "../../workerApi";
import pyScriptCode from "./worker_nma.py?raw";

export class NMAPredictor {
  async predict(
    input: PredictionInput
  ): Promise<DynamicModulusPredictorOutput> {
    return asyncRun(pyScriptCode, { prediction_input: input});
  }
}
