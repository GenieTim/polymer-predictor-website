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
  logit_vars_index: number[];
  cont_vars_index: number[];
  scale_vars_index: number[];
  logit_epsilon: number;
  log_y: boolean;
  standard_scaler: StandardScaler;
}

interface TargetScalerData {
  type: string;
  log_vars_index: number[];
  log1p_vars_index: number[];
  logit_vars_index: number[];
  exclude_vars_index: number[];
  logit_epsilon: number;
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
  private logitVarsIndex: number[];
  private contVarsIndex: number[];
  private scaleVarsIndex: number[];
  private logitEpsilon: number;
  private logY: boolean;
  private standardScaler: StandardScaler;

  constructor(scalerData: CustomScalerData) {
    this.binVarsIndex = scalerData.bin_vars_index;
    this.logitVarsIndex = scalerData.logit_vars_index;
    this.contVarsIndex = scalerData.cont_vars_index;
    this.scaleVarsIndex = scalerData.scale_vars_index;
    this.logitEpsilon = scalerData.logit_epsilon;
    this.logY = scalerData.log_y;
    this.standardScaler = scalerData.standard_scaler;
  }

  /**
   * Apply logit transformation: logit(x) = log(x / (1-x))
   * Clips to [epsilon, 1-epsilon] to avoid infinities.
   */
  private applyLogit(x: number): number {
    const xClipped = Math.max(
      this.logitEpsilon,
      Math.min(1 - this.logitEpsilon, x)
    );
    return Math.log(xClipped / (1 - xClipped));
  }

  /**
   * Transform the data using the fitted scaler.
   * 
   * IMPORTANT: This preserves the original column order of the input data.
   * Binary variables remain unchanged at their original positions.
   * Logit transformation is applied to bounded [0,1] variables before scaling.
   * StandardScaler is applied to logit + continuous variables.
   */
  transform(inputData: number[]): number[] {
    // inputData should be an array with values in the same order as input_features
    const result = [...inputData]; // Copy to preserve original order

    // Apply logit transformation to bounded [0,1] variables
    for (const idx of this.logitVarsIndex) {
      result[idx] = this.applyLogit(result[idx]);
    }

    // Apply StandardScaler to variables that need scaling (logit + continuous)
    if (
      this.scaleVarsIndex.length > 0 &&
      this.standardScaler.mean_ &&
      this.standardScaler.scale_
    ) {
      for (let i = 0; i < this.scaleVarsIndex.length; i++) {
        const idx = this.scaleVarsIndex[i];
        const mean = this.standardScaler.mean_[i];
        const scale = this.standardScaler.scale_[i];
        result[idx] = (result[idx] - mean) / scale;
      }
    }

    // Binary variables remain unchanged at their original positions
    return result;
  }
}

export class TargetScaler {
  private logVarsIndex: number[];
  private log1pVarsIndex: number[];
  private logitVarsIndex: number[];
  private excludeVarsIndex: number[];
  private logitEpsilon: number;
  private standardScaler: StandardScaler;

  constructor(scalerData: TargetScalerData) {
    this.logVarsIndex = scalerData.log_vars_index;
    this.log1pVarsIndex = scalerData.log1p_vars_index;
    this.logitVarsIndex = scalerData.logit_vars_index;
    this.excludeVarsIndex = scalerData.exclude_vars_index;
    this.logitEpsilon = scalerData.logit_epsilon;
    this.standardScaler = scalerData.standard_scaler;
  }

  /**
   * Apply inverse logit (sigmoid): sigmoid(y) = 1 / (1 + exp(-y))
   * This automatically constrains output to [0, 1].
   */
  private applyInverseLogit(y: number): number {
    // Clip to prevent overflow in exp
    const yClipped = Math.max(-500, Math.min(500, y));
    return 1.0 / (1.0 + Math.exp(-yClipped));
  }

  /**
   * Inverse transform the data using the fitted scaler.
   * 
   * IMPORTANT: This preserves the original column order of the input data.
   * Applies inverse StandardScaler, then inverse transformations (exp, expm1, sigmoid).
   */
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
      // Clip to prevent overflow
      const clipped = Math.min(result[idx], 700);
      result[idx] = Math.exp(clipped);
    }

    // Apply expm1() to log1p-transformed variables
    for (const idx of this.log1pVarsIndex) {
      // Clip to prevent overflow
      const clipped = Math.min(result[idx], 700);
      result[idx] = Math.expm1(clipped);
    }

    // Apply inverse logit (sigmoid) to bounded [0,1] variables
    for (const idx of this.logitVarsIndex) {
      result[idx] = this.applyInverseLogit(result[idx]);
    }

    return result;
  }
}
