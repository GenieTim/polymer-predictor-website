#!/usr/bin/env python


import warnings

import numpy as np
from pint import UnitRegistry
from pylimer_tools.generate_network import generate_structure
from pylimer_tools.io.bead_spring_parameter_provider import (
    Parameters, get_gaussian_parameters_for_polymer)
from pylimer_tools_cpp import NormalModeAnalyzer

crosslink_type = 2
same_strand_cutoff = 0.0

ureg = UnitRegistry()
# register alias for JavaScript Unit library
ureg.define("tempK = 1 K")
ureg.define("cm3 = 1 cm^3")
ureg.define("nm2 = 1 nm^2")
ureg.define("kg2 = 1 kg^2")


def parse_quantities_from_js(input_dict: dict):
    """
    Convert the JavaScript-style object to a dictionary of pint quantities.
    """
    output_dict = {}
    for key, value in input_dict.items():
        if isinstance(value, (int, float, str, list)):
            output_dict[key] = value
        elif "value" in value and "unit" in value:
            output_dict[key] = ureg.Quantity(value["value"], value["unit"])
        else:
            warnings.warn(f"Unexpected type for key {key}: {type(value)}")
            output_dict[key] = value
    return output_dict


def prediction_input_to_parameters(prediction_input: dict) -> Parameters:
    """
    Convert PredictionInput to Parameters object.
    """
    # return Parameters(
    #     {
    #         "R02": prediction_input.mean_squared_bead_distance,
    #         "Mw": prediction_input.bead_mass,
    #         "<b>": prediction_input.get_mean_bead_distance(),
    #         "<b^2>": prediction_input.mean_squared_bead_distance,
    #         "rho": prediction_input.density,
    #         "Ge": prediction_input.plateau_modulus,
    #         "T": prediction_input.temperature,
    #         "distance_units": 1 * ureg("nm"),
    #         "kb": 1.380649e-23 * ureg.joule / ureg.kelvin,
    #     },
    #     ureg,
    #     prediction_input.polymer_name,
    # )
    return get_gaussian_parameters_for_polymer(prediction_input["polymer_name"])


def predict_normal_mode_results(prediction_input_dict: dict) -> dict:
    """
    Compute ANT data for given parameters.
    """
    prediction_input_dict = parse_quantities_from_js(prediction_input_dict)
    max_n_beads = 5e3

    # scale system down if too large
    n_total_beads = prediction_input_dict["n_beads_total"]
    if n_total_beads > max_n_beads:
        scale_factor = max_n_beads / n_total_beads
        # reduce the number of chains
        prediction_input_dict["n_bifunctional_chains"] = int(
            prediction_input_dict["n_bifunctional_chains"] * scale_factor
        )
        prediction_input_dict["n_monofunctional_chains"] = int(
            prediction_input_dict["n_monofunctional_chains"] * scale_factor
        )
        prediction_input_dict["n_zerofunctional_chains"] = int(
            prediction_input_dict["n_zerofunctional_chains"] * scale_factor
        )
        prediction_input_dict["n_chains_crosslinks"] = int(
            prediction_input_dict["n_chains_crosslinks"] * scale_factor
        )

    universe = generate_structure(
        params=prediction_input_to_parameters(prediction_input_dict),
        n_beads_per_chain_1=prediction_input_dict["n_beads_bifunctional"],
        n_chains_1=prediction_input_dict["n_bifunctional_chains"],
        n_mono_beads_per_chain=prediction_input_dict["n_beads_monofunctional"],
        n_mono_chains=prediction_input_dict["n_monofunctional_chains"],
        target_f=prediction_input_dict["crosslink_functionality"],
        target_p=prediction_input_dict["crosslink_conversion"],
        n_solvent_chains=prediction_input_dict["n_zerofunctional_chains"],
        n_beads_per_solvent_chain=prediction_input_dict["n_beads_zerofunctional"],
        n_beads_per_xlink=prediction_input_dict["n_beads_xlinks"],
        remove_wsol=prediction_input_dict["extract_solvent_before_measurement"],
        disable_primary_loops=prediction_input_dict["disable_primary_loops"],
        disable_secondary_loops=prediction_input_dict["disable_secondary_loops"],
        functionalize_discrete=prediction_input_dict["functionalize_discrete"],
        n_chains_crosslinkers=prediction_input_dict["n_chains_crosslinks"],
    )

    edges = universe.get_edges()
    nma = NormalModeAnalyzer(
        spring_from=edges["edge_from"],
        spring_to=edges["edge_to"],
    )

    nma.find_all_eigenvalues()

    frequencies = np.logspace(-5, 5, num=1000)
    return {
        "frequencies": frequencies,
        "storage_modulus": nma.evaluate_storage_modulus(frequencies),
        "loss_modulus": nma.evaluate_loss_modulus(frequencies),
    }


# As this script is run using pyodide,
# prediction_input should be hydrated from there
assert (
    prediction_input is not None
), "PredictionInput must not be None"  # pyright: ignore[reportUndefinedVariable]
# Actual script, as called from pyodide
results = predict_normal_mode_results(prediction_input.as_object_map(hereditary=True))
# Final statement is an expression -> value is returned to JavaScript
{
    "frequencies": results["frequencies"].tolist(),
    "g_prime": results["storage_modulus"].tolist(),
    "g_double_prime": results["loss_modulus"].tolist(),
}  # pyright: ignore[reportUnusedExpression]
