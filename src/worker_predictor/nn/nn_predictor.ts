import type { PredictionInput } from "../../entity/PredictionInput";
import { ModulusPredictionOutput } from "../../entity/PredictionOutput";
import type { Predictor } from "../predictor";
import Qty from "js-quantities";
import * as ort from "onnxruntime-web";

export class NNPredictor implements Predictor {
  private session: ort.InferenceSession | null = null;
  private modelPath =
    "/models/m-remove_wsol_False_entanglements_as_springs_False_has_solvent_False_polymer_type_pdms_architecture_1xlink-without-mono.onnx";

  private async loadModel(): Promise<ort.InferenceSession> {
    if (this.session === null) {
      try {
        this.session = await ort.InferenceSession.create(this.modelPath);
      } catch (error) {
        throw new Error(`Failed to load ONNX model: ${error}`);
      }
    }
    return this.session;
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
      ["temperature [K]", (input) => input.temperature.to("K").scalar],
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
    input: PredictionInput
  ): Promise<Record<string, ort.Tensor>> {
    // Load the model to access input names
    const session = await this.loadModel();

    // Get the feature mapping
    const featureMapping = this.createFeatureMapping();

    // Create separate tensors for each input instead of concatenating
    const feeds: Record<string, ort.Tensor> = {};

    for (const inputName of session.inputNames) {
      const extractFunction = featureMapping.get(inputName);
      if (extractFunction) {
        const value = extractFunction(input);
        // Create individual tensor for each input
        const inputTensor = new ort.Tensor(
          "float32",
          new Float32Array([value]),
          [1, 1]
        );
        feeds[inputName] = inputTensor;
      } else {
        throw new Error(`Unknown input feature: ${inputName}`);
      }
    }

    return feeds;

    // Build features array based on the model's input names
    const features: number[] = [];

    for (const inputName of session.inputNames) {
      const extractFunction = featureMapping.get(inputName);
      if (extractFunction) {
        features.push(extractFunction(input));
      } else {
        throw new Error(
          `Unknown input feature: ${inputName}. Available mappings: ${Array.from(
            featureMapping.keys()
          ).join(", ")}`
        );
      }
    }

    // Create input tensor with the correct feature order
    const inputTensor = new ort.Tensor("float32", new Float32Array(features), [
      1,
      features.length,
    ]);

    // Use the first input name from the session (assuming single input model)
    const inputName = session.inputNames[0];
    return { [inputName]: inputTensor };
  }

  private processOutput(
    outputs: ort.InferenceSession.OnnxValueMapType
  ): ModulusPredictionOutput {
    // Extract the output tensor
    // Common output names are 'output', 'y', or specific names like 'predictions'
    const outputNames = Object.keys(outputs);
    if (outputNames.length === 0) {
      throw new Error("No outputs received from ONNX model");
    }

    const outputTensor = outputs[outputNames[0]] as ort.Tensor;
    const outputData = outputTensor.data as Float32Array;

    // Assuming the model outputs 4 values: [phantom_modulus, entanglement_modulus, w_soluble, w_dangling]
    if (outputData.length < 4) {
      throw new Error(
        `Expected at least 4 output values, got ${outputData.length}`
      );
    }

    const result = new ModulusPredictionOutput();
    result.phantom_modulus = Qty(outputData[0], "MPa");
    result.entanglement_modulus = Qty(outputData[1], "MPa");
    result.w_soluble = Qty(outputData[2], "");
    result.w_dangling = Qty(outputData[3], "");

    return result;
  }

  async predict(input: PredictionInput): Promise<ModulusPredictionOutput> {
    try {
      // Load the model
      const session = await this.loadModel();

      // Prepare input data
      const feeds = await this.prepareInput(input);

      // Run inference
      const results = await session.run(feeds);

      // Process and return output
      return this.processOutput(results);
    } catch (error) {
      throw new Error(`Neural network prediction failed: ${error}`);
    }
  }
}
