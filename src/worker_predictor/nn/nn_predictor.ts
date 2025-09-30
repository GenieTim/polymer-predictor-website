import type { PredictionInput } from "../../entity/PredictionInput";
import { ModulusPredictionOutput } from "../../entity/PredictionOutput";
import type { Predictor } from "../predictor";
import Qty from "js-quantities";
import * as ort from "onnxruntime-web";
import { CustomScaler, TargetScaler, type ModelMetadata } from "./scaler";

interface ModelConfig {
  modelPath: string;
  metadataPath: string;
}

/**
 * Neural Network Predictor that automatically selects the optimal model based on input parameters.
 *
 * This predictor manages three different ONNX models:
 * - General fallback model (m-): Handles all polymer types and configurations (20 features)
 * - PDMS long-xlinks model: Optimized for PDMS with multiple crosslinks (9 features)
 * - PDMS 1xlink-without-mono model: Optimized for PDMS with single crosslinks and no monofunctional chains (6 features)
 *
 * The predictor uses caching to avoid reloading models and maintains separate scalers for each model.
 * Models are selected automatically based on polymer type and structural parameters for optimal accuracy.
 */
export class NNPredictor implements Predictor {
  // Cache for loaded models and metadata
  private modelCache = new Map<string, ort.InferenceSession>();
  private metadataCache = new Map<string, ModelMetadata>();
  private scalerCache = new Map<
    string,
    { input: CustomScaler; target: TargetScaler }
  >();

  // Current model configuration
  private currentConfig: ModelConfig | null = null;

  constructor() {
    // No longer hardcode model paths - they will be selected dynamically
  }

  /**
   * Selects the appropriate neural network model based on input parameters.
   *
   * The model selection logic prioritizes specialized models for PDMS polymers:
   * 1. Use 1xlink-without-mono model for PDMS with single crosslinks and no monofunctional chains
   * 2. Use long-xlinks model for PDMS with multiple crosslinks
   * 3. Use general fallback model for all other cases (non-PDMS or other configurations)
   *
   * @param input - The prediction input containing polymer parameters
   * @returns ModelConfig object with paths to the selected model and metadata files
   */
  private selectModel(input: PredictionInput): ModelConfig {
    // Check if it's PDMS polymer type
    const isPDMS = input.polymer_name.toLowerCase().includes("pdms");

    if (
      isPDMS &&
      !input.extract_solvent_before_measurement &&
      !input.functionalize_discrete &&
      0 == input.n_zerofunctional_chains
    ) {
      // For PDMS: n_beads_xlinks = 1 and no monofunctional chains
      // Uses specialized model trained on subset with fewer parameters for better performance
      if (input.n_beads_xlinks === 1 && input.n_monofunctional_chains === 0) {
        return {
          modelPath:
            "/models/m-remove_wsol_False_entanglements_as_springs_False_has_solvent_False_polymer_type_pdms_architecture_1xlink-without-mono.onnx",
          metadataPath:
            "/models/m-remove_wsol_False_entanglements_as_springs_False_has_solvent_False_polymer_type_pdms_architecture_1xlink-without-mono_metadata.json",
        };
      }
      // For PDMS: n_beads_xlinks > 1
      // Uses specialized model for long crosslink configurations
      else if (input.n_beads_xlinks > 1) {
        return {
          modelPath:
            "/models/m-remove_wsol_False_functionalize_discrete_False_entanglements_as_springs_False_has_solvent_False_polymer_type_pdms_architecture_long-xlinks.onnx",
          metadataPath:
            "/models/m-remove_wsol_False_functionalize_discrete_False_entanglements_as_springs_False_has_solvent_False_polymer_type_pdms_architecture_long-xlinks_metadata.json",
        };
      }
    }

    // Fallback to general model for non-PDMS polymers or other PDMS configurations
    return {
      modelPath: "/models/m-.onnx",
      metadataPath: "/models/m-_metadata.json",
    };
  }

  private async loadModel(config: ModelConfig): Promise<ort.InferenceSession> {
    // Check if model is already cached
    if (!this.modelCache.has(config.modelPath)) {
      try {
        const session = await ort.InferenceSession.create(config.modelPath);
        this.modelCache.set(config.modelPath, session);
      } catch (error) {
        throw new Error(
          `Failed to load ONNX model from ${config.modelPath}: ${error}`
        );
      }
    }
    return this.modelCache.get(config.modelPath)!;
  }

  private async loadMetadata(config: ModelConfig): Promise<ModelMetadata> {
    // Check if metadata is already cached
    if (!this.metadataCache.has(config.metadataPath)) {
      try {
        const response = await fetch(config.metadataPath);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const metadata = (await response.json()) as ModelMetadata;
        this.metadataCache.set(config.metadataPath, metadata);

        // Initialize and cache scalers
        const inputScaler = new CustomScaler(metadata.input_scaler);
        const targetScaler = new TargetScaler(metadata.target_scaler);
        this.scalerCache.set(config.metadataPath, {
          input: inputScaler,
          target: targetScaler,
        });
      } catch (error) {
        throw new Error(
          `Failed to load model metadata from ${config.metadataPath}: ${error}`
        );
      }
    }
    return this.metadataCache.get(config.metadataPath)!;
  }

  private createFeatureMapping(): Map<
    string,
    (input: PredictionInput) => number
  > {
    // Map from NN input names to functions that extract the corresponding value from PredictionInput
    return new Map([
      ["r", (input) => input.stoichiometric_imbalance],
      ["p", (input) => input.crosslink_conversion],
      ["b2", (input) => input.b2],
      ["ge_1 [MPa]", (input) => input.plateau_modulus.to("MPa").scalar],
      ["temperature [K]", (input) => input.temperature.to("kelvin").scalar],
      ["density [g/cm^3]", (input) => input.density.to("g/cm^3").scalar],
      ["param's <b> [nm]", (input) => input.mean_bead_distance.to("nm").scalar],
      [
        "param's <b^2> [nm^2]",
        (input) => input.mean_squared_bead_distance.to("nm^2").scalar,
      ],
      [
        "remove_wsol",
        (input) => (input.extract_solvent_before_measurement ? 1 : 0),
      ],
      ["param's Mw [kg/mol]", (input) => input.bead_mass.to("kg/mol").scalar],
      [
        "Mw [kg/mol]",
        (input) =>
          input.bead_mass.to("kg/mol").scalar * input.n_beads_bifunctional,
      ],
      [
        "Mw [kg/mol] monofunctional chains",
        (input) =>
          input.bead_mass.to("kg/mol").scalar * input.n_beads_monofunctional,
      ],
      [
        "Mw [kg/mol] solvent chains",
        (input) =>
          input.bead_mass.to("kg/mol").scalar * input.n_beads_zerofunctional,
      ],
      [
        "Mw [kg/mol] xlink chains",
        (input) => input.bead_mass.to("kg/mol").scalar * input.n_beads_xlinks,
      ],
      [
        "functionality_per_xlink_chain",
        (input) => input.crosslink_functionality,
      ],
      [
        "functionalize_discrete",
        (input) => (input.functionalize_discrete ? 1 : 0),
      ],
      [
        "solvent_fraction_of_beads",
        (input) => input.total_n_beads_solvent / input.n_beads_total,
      ],
      [
        "monofunctional_fraction_of_beads",
        (input) => input.total_n_beads_monofunctional / input.n_beads_total,
      ],
      [
        "bifunctional_fraction_of_beads",
        (input) => input.total_n_beads_bifunctional / input.n_beads_total,
      ],
      [
        "entanglement_sampling_cutoff [nm]",
        (input) => input.entanglement_sampling_cutoff.to("nm").scalar,
      ],
      [
        "n_chains_total",
        (input) =>
          input.n_bifunctional_chains +
          input.n_monofunctional_chains +
          input.n_zerofunctional_chains +
          input.n_chains_crosslinks,
      ],
      ["entanglements_as_springs", (input) => 0],
    ]);
  }

  private async prepareInput(
    input: PredictionInput,
    config: ModelConfig
  ): Promise<Record<string, ort.Tensor>> {
    // Load metadata to get feature order
    const metadata = await this.loadMetadata(config);

    // Get cached scalers
    const scalers = this.scalerCache.get(config.metadataPath);
    if (!scalers) {
      throw new Error("Input scaler not initialized");
    }

    // Get the feature mapping
    const featureMapping = this.createFeatureMapping();

    // Build features array based on the metadata's input_features order
    const features: number[] = [];

    for (const featureName of metadata.input_features) {
      const extractFunction = featureMapping.get(featureName);
      if (extractFunction) {
        features.push(extractFunction(input));
      } else {
        throw new Error(
          `Unknown input feature: ${featureName}. Available mappings: ${Array.from(
            featureMapping.keys()
          ).join(", ")}`
        );
      }
    }

    // Apply input scaling
    const scaledFeatures = scalers.input.transform(features);

    // Create input tensor with the correct feature order
    const inputTensor = new ort.Tensor(
      "float32",
      new Float32Array(scaledFeatures),
      [1, scaledFeatures.length]
    );

    // Load the model to get the correct input name
    const session = await this.loadModel(config);
    const inputName = session.inputNames[0]; // Use first (and likely only) input name

    return { [inputName]: inputTensor };
  }

  private processOutput(
    outputs: ort.InferenceSession.OnnxValueMapType,
    config: ModelConfig
  ): ModulusPredictionOutput {
    // Get cached scalers
    const scalers = this.scalerCache.get(config.metadataPath);
    if (!scalers) {
      throw new Error("Target scaler not initialized");
    }

    // Extract the output tensor
    const outputNames = Object.keys(outputs);
    if (outputNames.length === 0) {
      throw new Error("No outputs received from ONNX model");
    }

    const outputTensor = outputs[outputNames[0]] as ort.Tensor;
    const outputData = outputTensor.data as Float32Array;

    // Convert to regular array and apply inverse target scaling
    const scaledOutput = Array.from(outputData);
    const finalOutput = scalers.target.inverseTransform(scaledOutput);

    // Assuming the model outputs 4 values based on metadata output_features:
    // ["G [MPa] from gamma Mean, Entangled FB No Slipping", "Phantom, FB/FR, G_ANT [MPa]", "dangling_fraction Mean, Entangled FB No Slipping", "soluble_fraction Mean, Entangled FB No Slipping"]
    if (finalOutput.length < 4) {
      throw new Error(
        `Expected at least 4 output values, got ${finalOutput.length}`
      );
    }

    const result = new ModulusPredictionOutput();
    result.entanglement_modulus = Qty(finalOutput[0], "MPa"); // G [MPa] from gamma Mean, Entangled FB No Slipping
    result.phantom_modulus = Qty(finalOutput[1], "MPa"); // Phantom, FB/FR, G_ANT [MPa]
    result.w_dangling = Qty(finalOutput[2], ""); // dangling_fraction Mean, Entangled FB No Slipping
    result.w_soluble = Qty(finalOutput[3], ""); // soluble_fraction Mean, Entangled FB No Slipping

    return result;
  }

  async predict(input: PredictionInput): Promise<ModulusPredictionOutput> {
    try {
      // Select the appropriate model based on input parameters
      const config = this.selectModel(input);
      this.currentConfig = config;

      // Load the selected model and metadata
      const session = await this.loadModel(config);
      await this.loadMetadata(config); // Ensure metadata and scalers are loaded

      // Prepare input data (includes scaling)
      const feeds = await this.prepareInput(input, config);

      // Run inference
      const results = await session.run(feeds);

      // Process and return output (includes inverse scaling)
      return this.processOutput(results, config);
    } catch (error) {
      console.error("NN prediction error:", error);
      throw new Error(`Neural network prediction failed: ${error}`);
    }
  }
}
