/**
 * TypeScript implementation of scalers for ONNX models
 * This demonstrates how to apply the CustomScaler and TargetScaler transformations
 * that were serialized from the Python training process.
 */

interface StandardScaler {
  with_mean: boolean;
  with_std: boolean;
  mean_: number[];
  scale_: number[];
  var_: number[];
}

interface CustomScalerData {
  type: string;
  bin_vars_index: number[];
  cont_vars_index: number[];
  log_y: boolean;
  standard_scaler: StandardScaler;
}

interface TargetScalerData {
  type: string;
  log_vars_index: number[];
  log1p_vars_index: number[];
  exclude_vars_index: number[];
  standard_scaler: StandardScaler;
}

export interface ModelMetadata {
  input_features: string[];
  output_features: string[];
  model_key: string;
  input_size: number;
  output_size: number;
  input_scaler: CustomScalerData;
  target_scaler: TargetScalerData;
}

export class CustomScaler {
  private binVarsIndex: number[];
  private contVarsIndex: number[];
  private logY: boolean;
  private standardScaler: StandardScaler;

  constructor(scalerData: CustomScalerData) {
    this.binVarsIndex = scalerData.bin_vars_index;
    this.contVarsIndex = scalerData.cont_vars_index;
    this.logY = scalerData.log_y;
    this.standardScaler = scalerData.standard_scaler;
  }

  transform(inputData: number[]): number[] {
    // inputData should be an array with values in the same order as input_features
    const result = new Array<number>(inputData.length);

    // Copy binary variables unchanged (first in result array)
    for (let i = 0; i < this.binVarsIndex.length; i++) {
      const binIndex = this.binVarsIndex[i];
      result[i] = inputData[binIndex];
    }

    // Apply StandardScaler to continuous variables
    if (
      this.contVarsIndex &&
      this.standardScaler.mean_ &&
      this.standardScaler.scale_
    ) {
      const contStart = this.binVarsIndex.length;
      for (let i = 0; i < this.contVarsIndex.length; i++) {
        const contIndex = this.contVarsIndex[i];
        const mean = this.standardScaler.mean_[i];
        const scale = this.standardScaler.scale_[i];

        result[contStart + i] = (inputData[contIndex] - mean) / scale;
      }
    }

    return result;
  }
}

export class TargetScaler {
  private logVarsIndex: number[];
  private log1pVarsIndex: number[];
  private excludeVarsIndex: number[];
  private standardScaler: StandardScaler;

  constructor(scalerData: TargetScalerData) {
    this.logVarsIndex = scalerData.log_vars_index;
    this.log1pVarsIndex = scalerData.log1p_vars_index;
    this.excludeVarsIndex = scalerData.exclude_vars_index;
    this.standardScaler = scalerData.standard_scaler;
  }

  inverseTransform(scaledOutput: number[]): number[] {
    // scaledOutput should be an array of model predictions
    const result = [...scaledOutput]; // Copy the array

    // First, apply inverse StandardScaler to non-excluded variables
    if (this.standardScaler.mean_ && this.standardScaler.scale_) {
      const allIndices = Array.from({ length: result.length }, (_, i) => i);
      const scaleIndices = allIndices.filter(
        (i) => !this.excludeVarsIndex.includes(i)
      );

      for (let i = 0; i < scaleIndices.length; i++) {
        const idx = scaleIndices[i];
        const mean = this.standardScaler.mean_[i];
        const scale = this.standardScaler.scale_[i];

        result[idx] = result[idx] * scale + mean;
      }
    }

    // Apply exp() to log-transformed variables
    for (const idx of this.logVarsIndex) {
      result[idx] = Math.exp(result[idx]);
    }

    // Apply expm1() to log1p-transformed variables
    for (const idx of this.log1pVarsIndex) {
      result[idx] = Math.expm1(result[idx]);
    }

    return result;
  }
}
