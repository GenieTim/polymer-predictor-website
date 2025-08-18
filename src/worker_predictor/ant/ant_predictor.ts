import type { PredictionInput } from "../../entity/PredictionInput";
import type { ModulusPredictionOutput } from "../../entity/PredictionOutput";
import type { Predictor } from "../predictor";
import { asyncRun } from "../../workerApi";
import pyScriptCode from "./worker_ant.py?raw";

export class ANTPredictor implements Predictor {
  async predict(input: PredictionInput): Promise<ModulusPredictionOutput> {
    return asyncRun(pyScriptCode, { prediction_input: input });
  }
}
