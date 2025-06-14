#!/usr/bin/env python
import io
import os
import pickle
from typing import List

from termcolor import colored
import torch

from pylimerpredictor.models.prediction_input import PredictionInput

from .neural_network.config import fit_key, input_axes, output_axes
from .neural_network.custom_scaler import CustomScaler, TargetScaler
from .neural_network.my_nn import NeuralNetwork


class RenameUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        renamed_module = module
        if module == "custom_scaler":
            renamed_module = "pylimerpredictor.predictors.neural_network.custom_scaler"

        return super(RenameUnpickler, self).find_class(renamed_module, name)


def renamed_load(file_obj):
    return RenameUnpickler(file_obj).load()


def renamed_loads(pickled_bytes):
    file_obj = io.BytesIO(pickled_bytes)
    return renamed_load(file_obj)


def predict_nn_results(prediction_input: PredictionInput) -> dict:
    base_path = os.path.dirname(__file__)
    model_path = os.path.join(
        base_path, "neural_network", "final_model_{}.pth".format(fit_key)
    )
    scaler_path = os.path.join(
        base_path, "neural_network", "scaler_{}.pkl".format(fit_key)
    )

    model = NeuralNetwork()
    # load the trained model
    model.load_state_dict(
        torch.load(
            model_path,
            weights_only=True,
        )
    )
    model.eval()

    # Load the saved scaler
    with open(scaler_path, "rb") as f:
        scalers = renamed_load(f)  # pickle.load(f)
        scaler = scalers["standard"]
        assert isinstance(scaler, CustomScaler), "Expected CustomScaler instance"
        target_scaler = scalers["target"]
        assert isinstance(target_scaler, TargetScaler), "Expected TargetScaler instance"

    # Function to make a prediction
    def predict(input_values: List):
        input_tensor = scaler.transform([input_values])
        input_tensor = torch.tensor(input_tensor, dtype=torch.float32)
        with torch.no_grad():
            output = model(input_tensor)
        return target_scaler.inverse_transform(output.numpy())[0]

    input_value_translator = {
        "r": prediction_input.stoichiometric_imbalance,
        "p": prediction_input.crosslink_conversion,
        "b2": prediction_input.get_b2(),
        "ge_1 [MPa]": prediction_input.plateau_modulus.to("MPa").magnitude,
        "temperature [K]": prediction_input.temperature.to("K").magnitude,
        "density [g/cm^3]": prediction_input.density.to("g/cm^3").magnitude,
        "param's <b> [nm]": prediction_input.get_mean_bead_distance()
        .to("nm")
        .magnitude,
        "param's Mw [kg/mol]": prediction_input.bead_mass.to("kg/mol").magnitude,
        "Mw [kg/mol]": prediction_input.n_beads_bifunctional
        * prediction_input.bead_mass.to("kg/mol").magnitude,
        "Mw [kg/mol] monofunctional chains": prediction_input.n_beads_monofunctional
        * prediction_input.bead_mass.to("kg/mol").magnitude,
        "Mw [kg/mol] xlink chains": prediction_input.n_beads_xlinks
        * prediction_input.bead_mass.to("kg/mol").magnitude,
        "Mw [kg/mol] solvent chains": prediction_input.n_beads_zerofunctional
        * prediction_input.bead_mass.to("kg/mol").magnitude,
        "functionality_per_xlink_chain": int(prediction_input.crosslink_functionality),
        "functionalize_discrete": bool(prediction_input.functionalize_discrete),
        "remove_wsol": bool(prediction_input.extract_solvent_before_measurement),
        "solvent_fraction_of_beads": prediction_input.get_total_n_beads_solvent()
        / prediction_input.get_n_total_beads(),
        "monofunctional_fraction_of_beads": prediction_input.get_total_n_beads_monofunctional()
        / prediction_input.get_n_total_beads(),
        "bifunctional_fraction_of_beads": prediction_input.get_total_n_beads_bifunctional()
        / prediction_input.get_n_total_beads(),
        "crosslink_fraction_of_beads": prediction_input.get_total_n_beads_xlinks()
        / prediction_input.get_n_total_beads(),
        "entanglement_sampling_cutoff [nm]": prediction_input.entanglement_sampling_cutoff.to(
            "nm"
        ).magnitude,
    }

    assert all(label in input_value_translator for label in input_axes)
    predictions = predict([input_value_translator[k] for k in input_axes])

    print(colored("NN Predictions: {}".format(predictions), "green"))

    result_translator = {
        "g_eq": "G [MPa] from gamma Mean, Entangled FB No Slipping",
        "g_phantom": "Phantom, FB/FR, G_ANT [MPa]",
        "w_dangling": "dangling_fraction Mean, Entangled FB No Slipping",
        "w_soluble": "soluble_fraction Mean, Entangled FB No Slipping",
    }

    results = {}

    assert any(
        label in output_axes for label in result_translator.values()
    ), "No results to return, check the output axes and result translator."

    for key, label in result_translator.items():
        if label in output_axes:
            index = output_axes.index(label)
            results[key] = predictions[index]
        else:
            results[key] = None

    if "g_eq" in results and "g_phantom" in results:
        results["g_entangled"] = results["g_eq"] - results["g_phantom"]

    if "w_dangling" in results and "w_soluble" in results:
        results["w_backbone"] = 1 - results["w_dangling"] - results["w_soluble"]

    return results
