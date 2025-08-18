import type { PredictionInput } from "../entity/PredictionInput";
import type { ModulusPredictionOutput } from "../entity/PredictionOutput";

export interface Predictor {
  predict(input: PredictionInput): Promise<ModulusPredictionOutput>;
}
