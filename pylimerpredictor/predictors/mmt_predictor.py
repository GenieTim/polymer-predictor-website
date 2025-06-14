#!/usr/bin/env python

import warnings

from pylimer_tools.calc.miller_macosko_theory import (
    compute_modulus_decomposition,
    compute_weight_fraction_of_backbone,
    compute_weight_fraction_of_dangling_chains,
    compute_weight_fraction_of_soluble_material,
)
from quantityfield.units import ureg

from pylimerpredictor.models.prediction_input import PredictionInput

"""
Shortcut to acquire all data from MMT given some parameters.
"""


def predict_mmt_results(prediction_input: PredictionInput) -> dict:
    """
    Compute MMT data for given parameters.
    """
    r = prediction_input.stoichiometric_imbalance
    p = prediction_input.crosslink_conversion
    f = prediction_input.crosslink_functionality
    ge_1 = prediction_input.plateau_modulus
    temperature = prediction_input.temperature
    density = prediction_input.density
    Mw1 = prediction_input.n_beads_monofunctional * prediction_input.bead_mass
    Mw2 = prediction_input.n_beads_bifunctional * prediction_input.bead_mass
    MwX = prediction_input.n_beads_xlinks * prediction_input.bead_mass
    b2 = prediction_input.get_b2()

    n_chains = 1e7
    n_chains_mono = int((2 * n_chains * (1 - b2)) / b2)
    # require Mw1, Mw2, MwX to have the same units
    if (
        not isinstance(Mw1, ureg.Quantity)
        or not isinstance(Mw2, ureg.Quantity)
        or not isinstance(MwX, ureg.Quantity)
    ):
        raise ValueError("All Mw parameters must have the same units")

    if Mw1.check("[mass]/[substance]"):
        Na = 6.022e23 * ureg("1/mol")
        Mw1 = (Mw1 / Na).to("kg")
        Mw2 = (Mw2 / Na).to("kg")
        MwX = (MwX / Na).to("kg")

    assert Mw1.check("[mass]") and Mw2.check("[mass]") and MwX.check("[mass]")

    Mw_eff = (n_chains * Mw2 + n_chains_mono * Mw1) / (n_chains + n_chains_mono)
    data = {
        "Mw_eff [kg]": Mw_eff.to("kg").magnitude,
        "MMT nu [nm^-3]": (density / (Mw_eff)).to("nm^-3").magnitude,
    }
    try:
        G_MMT_phantom, G_MMT_entanglement, g_anm, g_pnm = compute_modulus_decomposition(
            network=None,
            crosslinker_type=2,
            r=r,
            p=p,
            f=f,
            g_e_1=ge_1,
            temperature=temperature,
            nu=(density / (Mw_eff)),
            ureg=ureg,
            b2=b2,
        )
    except ValueError as e:
        warnings.warn(f"Error computing modulus decomposition: {e}")
        return {}
    data["g_phantom"] = G_MMT_phantom.to("MPa").magnitude
    # TODO: this correction for b2 must be reconsidered
    b2_entanglement_correction = (
        ((Mw2 * n_chains) / (Mw1 * n_chains_mono + Mw2 * n_chains))
        .to("dimensionless")
        .magnitude
    )
    data["Mw b2 entanglement correction"] = b2_entanglement_correction
    data["g_entangled"] = (
        G_MMT_entanglement.to("MPa").magnitude * b2_entanglement_correction
    )
    data["g_eq"] = data["g_entangled"] + data["g_phantom"]
    data["g_anm"] = g_anm.to("MPa").magnitude
    data["g_pnm"] = g_pnm.to("MPa").magnitude
    functionality_per_type = {1: 2, 2: f, 4: 1}
    n_crosslinks = int(((n_chains * 2 + n_chains_mono) * r) / (f))
    total_weight = n_chains_mono * Mw1 + n_chains * Mw2 + n_crosslinks * MwX
    weight_fractions = {
        1: (n_chains * Mw2) / (total_weight),
        2: (n_crosslinks * MwX) / (total_weight),
        4: (n_chains_mono * Mw1) / (total_weight),
    }

    for k in weight_fractions.keys():
        data[f"MMT weight fraction of type {k}"] = weight_fractions[k]

    data["w_soluble"] = compute_weight_fraction_of_soluble_material(
        network=None,
        crosslinker_type=2,
        functionality_per_type=functionality_per_type,
        weight_fractions=weight_fractions,
        r=r,
        p=p,
        b2=b2,
    )
    data["w_backbone"] = compute_weight_fraction_of_backbone(
        network=None,
        crosslinker_type=2,
        functionality_per_type=functionality_per_type,
        weight_fractions=weight_fractions,
        r=r,
        p=p,
        b2=b2,
    )
    data["w_dangling"] = compute_weight_fraction_of_dangling_chains(
        network=None,
        crosslinker_type=2,
        functionality_per_type=functionality_per_type,
        weight_fractions=weight_fractions,
        r=r,
        p=p,
        b2=b2,
    )

    return data
