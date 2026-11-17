#!/usr/bin/env python

import math
import warnings

import numpy as np
from pint import UnitRegistry
from pylimer_tools.generate_network import prepare_structure_generation
from pylimer_tools.io.bead_spring_parameter_provider import (
    Parameters, get_gaussian_parameters_for_polymer)
from pylimer_tools_cpp import (MCUniverseGenerator,
                               StructureSimplificationMode)

crosslink_type = 2
same_strand_cutoff = 0.0

# As this script is run using pyodide,
# prediction_input should be hydrated from there
assert (
    prediction_input is not None
), "PredictionInput must not be None"  # pyright: ignore[reportUndefinedVariable]

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
        elif isinstance(value, dict) and "value" in value and "unit" in value:
            output_dict[key] = ureg.Quantity(value["value"], value["unit"])
        elif hasattr(value, "value") and hasattr(value, "unit"):
            output_dict[key] = ureg.Quantity(value.value, value.unit)
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
    return get_gaussian_parameters_for_polymer(prediction_input["polymer_name"], ureg=ureg)


def predict_ant_results(prediction_input: dict) -> dict:
    """
    Compute ANT data for given parameters.
    """
    prediction_input = parse_quantities_from_js(prediction_input)

    universe_generator = prepare_structure_generation(
        params=prediction_input_to_parameters(prediction_input),
        n_beads_per_chain_1=prediction_input["n_beads_bifunctional"],
        n_chains_1=prediction_input["n_bifunctional_chains"],
        n_mono_beads_per_chain=prediction_input["n_beads_monofunctional"],
        n_mono_chains=prediction_input["n_monofunctional_chains"],
        target_f=prediction_input["crosslink_functionality"],
        target_p=prediction_input["crosslink_conversion"],
        n_solvent_chains=prediction_input["n_zerofunctional_chains"],
        n_beads_per_solvent_chain=prediction_input["n_beads_zerofunctional"],
        n_beads_per_xlink=prediction_input["n_beads_xlinks"],
        remove_wsol=prediction_input["extract_solvent_before_measurement"],
        disable_primary_loops=prediction_input["disable_primary_loops"],
        disable_secondary_loops=prediction_input["disable_secondary_loops"],
        functionalize_discrete=prediction_input["functionalize_discrete"],
        n_chains_crosslinkers=prediction_input["n_chains_crosslinks"],
    )

    return analyse_network(universe_generator, prediction_input=prediction_input)


def analyse_network(
    universe_generator: MCUniverseGenerator, prediction_input: dict
) -> dict:
    """
    Runs force balance in phantom and entangled mode directly on the MCUniverseGenerator,
    avoiding full Universe materialization.
    """
    ge_1 = prediction_input["plateau_modulus"]
    r02_slope = prediction_input["mean_squared_bead_distance"]
    r02_slope_magnitude = r02_slope.to("nm^2").magnitude

    parameters = prediction_input_to_parameters(prediction_input)
    kbt = prediction_input["temperature"] * parameters.get("kb")
    gamma_conversion_factor = (
        (kbt / ((parameters.get("distance_units")) ** 3)).to("MPa").magnitude
    )

    entanglement_density = parameters.get_entanglement_density(ge_1)
    sampling_cutoff = prediction_input["entanglement_sampling_cutoff"]
    volume = universe_generator.get_box().get_volume()

    # Run force balance in phantom mode
    force_balance_phantom = universe_generator.get_force_balance2()
    force_balance_phantom.run_force_relaxation(
        simplification_mode=StructureSimplificationMode.NO_SIMPLIFICATION,
    )
    g_phantom = (
        gamma_conversion_factor
        * np.sum(force_balance_phantom.get_gamma_factors(r02_slope_magnitude))
        / volume
    )

    # Run force balance with on-demand entanglement sampling
    n_entanglements = entanglement_density * volume
    print(
        "Running force balance with entanglements, sampling {} entanglements in a V = {} with density = {}.".format(
            n_entanglements, volume, entanglement_density
        )
    )

    if int(n_entanglements) > 0:
        force_balance_base = universe_generator.get_force_balance2(
            nr_of_entanglements_to_sample=int(n_entanglements),
            upper_cutoff=sampling_cutoff.to(
                parameters.get("distance_units")
            ).magnitude,
            lower_cutoff=0.0,
            minimum_nr_of_entanglements=int(math.floor(n_entanglements * 0.95)),
            same_strand_cutoff=same_strand_cutoff,
            seed="",
            entanglements_as_springs=False,
            crosslinker_type=crosslink_type,
        )
    else:
        force_balance_base = universe_generator.get_force_balance2()

    assert force_balance_base.validate_network()
    print("Network valid before starting relaxation.")

    force_balance_base.run_force_relaxation(
        simplification_mode=StructureSimplificationMode.INACTIVE_THEN_X2F
    )

    g_ant = (
        gamma_conversion_factor
        * np.sum(force_balance_base.get_gamma_factors(r02_slope_magnitude))
        / volume
    )
    w_soluble = force_balance_base.get_soluble_weight_fraction()
    w_dangling = force_balance_base.get_dangling_weight_fraction()

    return {
        "g_ant": g_ant,
        "g_phantom": g_phantom,
        "g_entangled": g_ant - g_phantom,
        "w_soluble": w_soluble,
        "w_dangling": w_dangling,
        "w_backbone": 1.0 - w_soluble - w_dangling,
    }


# Actual script, as called from pyodide
input_data = (
    prediction_input.to_py()
    if hasattr(prediction_input, "to_py")
    else prediction_input.as_object_map(hereditary=True)
)
results = predict_ant_results(input_data)
# Reduce to what we care about
res = {
    "phantom_modulus": results.get("g_phantom"),
    "entanglement_modulus": results.get("g_entangled"),
    "w_soluble": results.get("w_soluble"),
    "w_dangling": results.get("w_dangling"),
}
for key, value in res.items():
    if isinstance(value, ureg.Quantity):
        res[key] = value.to("MPa").magnitude if "g_" in key else value.magnitude
for key, value in res.items():
    if isinstance(value, np.floating):
        res[key] = float(value)
# Final statement is an expression -> value is returned to JavaScript
res  # pyright: ignore[reportUnusedExpression]
