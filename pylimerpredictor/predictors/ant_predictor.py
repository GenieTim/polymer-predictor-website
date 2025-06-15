#!/usr/bin/env python

import datetime
import math
import time

import numpy as np
from pylimer_doctorate_utils.pdms_parameter_provider import Parameters
from pylimer_tools.calc.structure_analysis import compute_crosslinker_conversion
from pylimer_tools_cpp import (
    MEHPForceBalance2,
    MoleculeType,
    StructureSimplificationMode,
    Universe,
    version_information,
)
from quantityfield.units import ureg

from pylimerpredictor.models.prediction_input import PredictionInput

from .generate_mc_structure import generate_structure

crosslink_type = 2
same_strand_cutoff = 0.0


def prediction_input_to_parameters(prediction_input: PredictionInput) -> Parameters:
    """
    Convert PredictionInput to Parameters object.
    """
    return Parameters(
        {
            "R02": prediction_input.mean_squared_bead_distance,
            "Mw": prediction_input.bead_mass,
            "<b>": prediction_input.get_mean_bead_distance(),
            "<b^2>": prediction_input.mean_squared_bead_distance,
            "rho": prediction_input.density,
            "Ge": prediction_input.plateau_modulus,
            "T": prediction_input.temperature,
            "distance_units": 1 * ureg("nm"),
            "kb": 1.380649e-23 * ureg.joule / ureg.kelvin,
        },
        ureg,
        prediction_input.polymer_name,
    )


def predict_ant_results(prediction_input: PredictionInput) -> dict:
    """
    Compute ANT data for given parameters.
    """
    universe = generate_structure(
        params=prediction_input_to_parameters(prediction_input),
        n_beads_per_chain_1=prediction_input.n_beads_bifunctional,
        n_chains_1=prediction_input.n_bifunctional_chains,
        n_mono_beads_per_chain=prediction_input.n_beads_monofunctional,
        n_mono_chains=prediction_input.n_monofunctional_chains,
        target_f=prediction_input.crosslink_functionality,
        target_p=prediction_input.crosslink_conversion,
        n_solvent_chains=prediction_input.n_zerofunctional_chains,
        n_beads_per_solvent_chain=prediction_input.n_beads_zerofunctional,
        n_beads_per_xlink=prediction_input.n_beads_xlinks,
        remove_wsol=prediction_input.extract_solvent_before_measurement,
        disable_primary_loops=prediction_input.disable_primary_loops,
        disable_secondary_loops=prediction_input.disable_secondary_loops,
        functionalize_discrete=prediction_input.functionalize_discrete,
        n_chains_crosslinks=prediction_input.get_n_chains_crosslinks(),
    )

    results = analyse_universe(universe, prediction_input=prediction_input)
    results["g_ant"] = results["G [MPa] from gamma Mean, Entangled FB No Slipping"]
    results["g_phantom"] = results["Phantom, Force Balance, G_ANT [MPa]"]
    results["g_entangled"] = results["g_ant"] - results["g_phantom"]
    results["w_soluble"] = results["soluble_fraction Mean, Entangled FB No Slipping"]
    results["w_dangling"] = results["dangling_fraction Mean, Entangled FB No Slipping"]
    results["w_backbone"] = 1.0 - results["w_soluble"] - results["w_dangling"]
    return results


def analyse_universe(universe: Universe, prediction_input: PredictionInput) -> dict:
    """
    Runs force relaxation and force balance on a given structure.
    """
    # shortcuts
    ge_1 = prediction_input.plateau_modulus
    f = prediction_input.crosslink_functionality
    # prepare conversion factors
    r02_slope = prediction_input.mean_squared_bead_distance
    r02_slope_magnitude = r02_slope.to("nm^2").magnitude

    parameters = prediction_input_to_parameters(prediction_input)
    kbt = prediction_input.temperature * parameters.get("kb")
    gamma_conversion_factor = (
        (kbt / ((parameters.get("distance_units")) ** 3)).to("MPa").magnitude
    )
    stress_conversion = parameters.get_fb_stress_conversion()

    entanglement_density = parameters.get_entanglement_density(ge_1)
    sampling_cutoff = prediction_input.entanglement_sampling_cutoff

    start_time = time.time()
    molecules = universe.get_molecules(crosslink_type)
    universe_data = {
        "effective_f": universe.determine_effective_functionality_per_type()[
            crosslink_type
        ],
        "Volume [nm^3]": universe.get_volume()
        * ((parameters.get("distance_units")) ** 3).to("nm^3").magnitude,
        "entanglement_density": entanglement_density,
        "sampling_cutoff [nm]": sampling_cutoff.magnitude,
        "n_atoms": universe.get_nr_of_atoms(),
        "n_bonds": universe.get_nr_of_bonds(),
        "n_xlinks": len(universe.get_atoms_by_type(crosslink_type)),
        "n_molecules": len(molecules),
        "same_strand_cutoff": same_strand_cutoff,
        "stress_conversion": stress_conversion,
        "gamma_conversion_factor": gamma_conversion_factor,
        "crosslinker_conversion": compute_crosslinker_conversion(
            universe, crosslinker_type=crosslink_type, f=f
        ),
        "now": datetime.datetime.now().isoformat(),
        "pylimer_tools_v": version_information(),
        "entanglement_type": "link",
        # "loop_counts": universe.count_loop_lengths(
        #     3 * (np.max([m.get_nr_of_bonds() for m in molecules]) + 3)
        # ),
        "mean_molecule_n_bonds": np.mean([m.get_nr_of_bonds() for m in molecules]),
        # "cluster_atom_counts": [u.get_nr_of_atoms() for u in universe.get_clusters()],
        "<b> [nm]": (
            np.mean(universe.compute_bond_lengths()) * parameters.get("distance_units")
        )
        .to("nm")
        .magnitude,
        "<b^2> [nm^2]": (
            np.mean(np.square(universe.compute_bond_lengths()))
            * (parameters.get("distance_units") ** 2)
        )
        .to("nm^2")
        .magnitude,
        "<R_ee^2> [nm^2]": (
            universe.compute_mean_squared_end_to_end_distance(
                crosslinker_type=crosslink_type, derive_image_flags=True
            )
            * (parameters.get("distance_units") ** 2)
        )
        .to("nm^2")
        .magnitude,
        "<R_ee^2> [nm^2], 2 x-links only": (
            universe.compute_mean_squared_end_to_end_distance(
                crosslinker_type=crosslink_type,
                derive_image_flags=True,
                only_those_with_two_crosslinkers=True,
            )
            * (parameters.get("distance_units") ** 2)
        )
        .to("nm^2")
        .magnitude,
        "<R_ee^> [nm^2], no cross-links": (
            np.mean(
                [
                    (m.compute_end_to_end_distance_with_derived_image_flags() ** 2)
                    for m in molecules
                    if m.get_nr_of_bonds() > 1
                ]
            )
            * (parameters.get("distance_units") ** 2)
        )
        .to("nm^2")
        .magnitude,
        "<R_ee^2> [nm^2], 2 x-links only, excl. primary loops": (
            np.mean(
                [
                    m.compute_end_to_end_distance_with_derived_image_flags() ** 2
                    for m in universe.get_chains_with_crosslinker(crosslink_type)
                    if m.get_strand_type() == MoleculeType.NETWORK_STRAND
                ]
            )
            * (parameters.get("distance_units") ** 2)
        )
        .to("nm^2")
        .magnitude,
        "M_w [g/mol]": (
            np.mean(
                [
                    m.get_nr_of_bonds() + 2
                    for m in universe.get_molecules(crosslink_type)
                ]
            )
            * parameters.get("Mw")
        )
        .to("g/mol")
        .magnitude,
        "preparation_time": time.time() - start_time,
    }

    for degree in range(3, 9):
        universe_data["n_atoms_with_degree_" + str(degree)] = len(
            universe.get_atoms_by_degree(degree)
        )
    for type, count in universe.count_atom_types().items():
        universe_data["n_atoms_with_type_" + str(type)] = count

    # Run force relaxation in phantom mode
    # force_relaxation_phantom = MEHPForceRelaxation(
    #     universe, crosslinker_type=crosslink_type
    # )
    # while force_relaxation_phantom.requires_another_run():
    #     force_relaxation_phantom.run_force_relaxation()

    # universe_data["Phantom, Force Relaxation, G_ANT [MPa]"] = (
    #     gamma_conversion_factor
    #     * np.sum(force_relaxation_phantom.get_gamma_factors(r02_slope.magnitude))
    #     / universe.get_volume()
    # )
    # universe_data["Phantom, Force Relaxation, W_sol"] = (
    #     force_relaxation_phantom.get_soluble_weight_fraction()
    # )
    # universe_data["Phantom, Force Relaxation, W_dang"] = (
    #     force_relaxation_phantom.get_dangling_weight_fraction()
    # )

    # Run force balance in phantom mode
    force_balance_phantom = MEHPForceBalance2(universe, crosslinker_type=crosslink_type)
    force_balance_phantom.run_force_relaxation(
        simplification_mode=StructureSimplificationMode.ALL_TIM,
    )
    universe_data["Phantom, Force Balance, G_ANT [MPa]"] = (
        gamma_conversion_factor
        * np.sum(force_balance_phantom.get_gamma_factors(r02_slope_magnitude))
        / universe.get_volume()
    )
    universe_data["Phantom, Force Balance, W_sol"] = (
        force_balance_phantom.get_soluble_weight_fraction()
    )
    universe_data["Phantom, Force Balance, W_dang"] = (
        force_balance_phantom.get_dangling_weight_fraction()
    )

    for dir in range(3):
        universe_data["Phantom, n active springs in {}".format("xyz"[dir])] = (
            force_balance_phantom.get_nr_of_active_springs_in_dir(direction=dir)
        )
        universe_data["Phantom, Force Balance, G_ANT_{} [MPa]".format("xyz"[dir])] = (
            gamma_conversion_factor
            * np.sum(
                force_balance_phantom.get_gamma_factors_in_dir(
                    r02_slope_magnitude, direction=dir
                )
            )
            / universe.get_volume()
        )

    resulting_universe = force_balance_phantom.get_crosslinker_universe()

    for degree in range(3, 9):
        universe_data["after_phantom_fb_n_atoms_with_degree_" + str(degree)] = len(
            resulting_universe.get_atoms_by_degree(degree)
        )

    # Run force balance with entanglements
    n_entanglements = entanglement_density * universe.get_volume()
    print(
        "Running force balance with entanglements, sampling {} entanglements in a V = {} with density = {}.".format(
            n_entanglements, universe.get_volume(), entanglement_density
        )
    )

    meanable_values = {}
    meanable_funs = {
        "n_steps_done": lambda fb: fb.get_nr_of_iterations(),
        "dangling_fraction": lambda fb: fb.get_dangling_weight_fraction(),
        "soluble_fraction": lambda fb: fb.get_soluble_weight_fraction(),
        "n_active_springs": lambda fb: fb.get_nr_of_active_springs(),
        "n_active_springs_x": lambda fb: fb.get_nr_of_active_springs_in_dir(
            direction=0
        ),
        "n_active_springs_y": lambda fb: fb.get_nr_of_active_springs_in_dir(
            direction=1
        ),
        "n_active_springs_z": lambda fb: fb.get_nr_of_active_springs_in_dir(
            direction=2
        ),
        "n_springs": lambda fb: fb.get_nr_of_springs(),
        "n_active_nodes": lambda fb: fb.get_nr_of_active_nodes(),
        "displacement_residual_norm": lambda fb: fb.get_displacement_residual_norm(),
        "G [MPa] from gamma": lambda fb: (
            gamma_conversion_factor
            * np.sum(fb.get_gamma_factors(r02_slope_magnitude))
            / universe.get_volume()
        ),
        "G [MPa] from gamma in x": lambda fb: (
            gamma_conversion_factor
            * np.sum(fb.get_gamma_factors_in_dir(r02_slope_magnitude, direction=0))
            / universe.get_volume()
        ),
        "G [MPa] from gamma in y": lambda fb: (
            gamma_conversion_factor
            * np.sum(fb.get_gamma_factors_in_dir(r02_slope_magnitude, direction=1))
            / universe.get_volume()
        ),
        "G [MPa] from gamma in z": lambda fb: (
            gamma_conversion_factor
            * np.sum(fb.get_gamma_factors_in_dir(r02_slope_magnitude, direction=2))
            / universe.get_volume()
        ),
    }

    for key in meanable_funs.keys():
        meanable_values[key] = []

    # for _ in range(3):
    for _ in range(1):
        force_balance_base = MEHPForceBalance2(
            universe,
            nr_of_entanglements_to_sample=int(n_entanglements),
            minimum_nr_of_sliplinks=int(math.floor(n_entanglements * 0.95)),
            crosslinker_type=crosslink_type,
            is_2d=False,
            lower_sampling_cutoff=0.0,
            upper_sampling_cutoff=sampling_cutoff.to(
                parameters.get("distance_units")
            ).magnitude,
            same_strand_cutoff=same_strand_cutoff,
            seed="",
        )

        assert force_balance_base.validate_network()
        print("Network valid before starting relaxation.")

        force_balance_base.run_force_relaxation(
            simplification_mode=StructureSimplificationMode.ALL_TIM
        )

        for key in meanable_funs.keys():
            meanable_values[key].append(meanable_funs[key](force_balance_base))

    for key in meanable_funs.keys():
        universe_data[f"{key} Mean, Entangled FB No Slipping"] = np.mean(
            meanable_values[key]
        )
        universe_data[f"{key} Std Dev, Entangled FB No Slipping"] = np.std(
            meanable_values[key]
        )
        universe_data[f"{key} Min, Entangled FB No Slipping"] = np.min(
            meanable_values[key]
        )
        universe_data[f"{key} Max, Entangled FB No Slipping"] = np.max(
            meanable_values[key]
        )

    universe_data["Total Computation Time [s]"] = time.time() - start_time
    return universe_data
