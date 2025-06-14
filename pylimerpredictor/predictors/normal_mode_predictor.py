#!/usr/bin/env python


import numpy as np
from pylimer_tools_cpp import NormalModeAnalyzer

from pylimerpredictor.models.prediction_input import PredictionInput
from pylimerpredictor.predictors.ant_predictor import prediction_input_to_parameters

from .generate_mc_structure import generate_structure

crosslink_type = 2
same_strand_cutoff = 0.0


def predict_normal_mode_results(prediction_input: PredictionInput) -> dict:
    """
    Compute ANT data for given parameters.
    """
    max_n_beads = 3e3

    # scale system down if too large
    n_total_beads = prediction_input.get_n_beads_total()
    if n_total_beads > max_n_beads:
        scale_factor = max_n_beads / n_total_beads
        # reduce the number of chains
        prediction_input.n_bifunctional_chains = int(
            prediction_input.n_bifunctional_chains * scale_factor
        )
        prediction_input.n_monofunctional_chains = int(
            prediction_input.n_monofunctional_chains * scale_factor
        )
        prediction_input.n_zerofunctional_chains = int(
            prediction_input.n_zerofunctional_chains * scale_factor
        )

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
