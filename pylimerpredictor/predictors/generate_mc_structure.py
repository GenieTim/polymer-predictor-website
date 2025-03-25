#!/usr/bin/env python

"""
Uses an MC procedure to produce an MC structure with a given number of crosslinks and a given number of chains.
"""

import math
import time

import numpy as np
from pylimer_tools.calc.structure_analysis import (
    compute_crosslinker_conversion,
    compute_stoichiometric_imbalance,
)
from pylimer_tools_cpp import MCUniverseGenerator, Universe
from termcolor import colored

###
# Configuration
###
normal_atom_type = 1
crosslink_type = 2
monofunctional_chains_type = 4

run_force_relaxation = False
###


def print_with_time(message: str) -> None:
    print(
        message
        + " at "
        + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    )


def generate_structure(
    n_beads_per_chain: int,
    target_p: float = None,
    target_wsol: float = None,
    target_r: float = 1.0,
    target_f: int = 4,
    n_chains: int = 10000,
    n_mono_chains: int = 0,
    n_mono_beads_per_chain: int = 0,
    remove_wsol: bool = False,
    disable_primary_loops: bool = False,
    disable_secondary_loops: bool = False,
    z_score_std_mult: float = 3.0,
    bead_density: float = 1.0,
    mean_squared_bead_distance: float = 1.0,
) -> Universe:
    if target_p is None and target_wsol is None:
        raise ValueError("target_p or target_wsol must be provided")
    if target_p is not None and target_wsol is not None:
        raise ValueError("Only one of target_p and target_wsol should be provided")

    n_beads_per_chain = n_beads_per_chain
    n_crosslinks = int(((n_chains * 2 + n_mono_chains) * target_r) / (target_f))

    if target_p is not None:
        target_p = min(
            target_p,
            0.9999999 * (n_chains * 2 + n_mono_chains) / (n_crosslinks * target_f),
        )

    # the mass is in the segments / bonds
    volume = (
        (n_beads_per_chain) * n_chains
        + (n_mono_beads_per_chain) * n_mono_chains
        + (n_crosslinks)
    ) / bead_density
    box_l = np.cbrt(volume)

    # randomly sample chains
    universe_generator = MCUniverseGenerator(box_l, box_l, box_l)
    universe_generator.set_mean_squared_bead_distance(mean_squared_bead_distance)

    if disable_primary_loops:
        universe_generator.config_primary_loop_probability(0.0)
    if disable_secondary_loops:
        universe_generator.config_secondary_loop_probability(0.0)

    assert math.isclose(
        universe_generator.get_mean_squared_bead_distance(),
        mean_squared_bead_distance,
        rel_tol=0.1,
    )
    universe_generator.config_nr_of_mc_steps(0)

    universe_generator.add_crosslinkers(
        nr_of_crosslinkers=n_crosslinks,
        crosslinker_type=crosslink_type,
        crosslinker_functionality=target_f,
    )
    if n_mono_chains > 0:
        universe_generator.add_monofunctional_strands(
            n_mono_chains,
            np.repeat(n_mono_beads_per_chain, n_mono_chains),
            monofunctional_chains_type,
        )
    universe_generator.add_strands(
        n_chains,
        np.repeat(n_beads_per_chain, n_chains),
        strand_atom_type=normal_atom_type,
    )
    universe_generator.use_zscore_max_distance(
        z_score_std_mult, mean_squared_bead_distance
    )

    print_with_time(colored("Linking strands", "grey"))
    if target_p is not None:
        assert target_wsol is None
        universe_generator.link_strands_to_conversion(
            crosslinker_conversion=target_p,
        )
    else:
        assert target_wsol is not None
        universe_generator.link_strands_to_soluble_fraction(
            target_wsol,
        )

    if run_force_relaxation:
        universe_generator.relax_crosslinks()

    if remove_wsol:
        universe_generator.remove_soluble_fraction(True)

    print_with_time(colored("Sampling beads", "grey"))
    universe = universe_generator.get_universe()

    # some final additional info
    universe.set_masses(
        {
            crosslink_type: 1.0,
            normal_atom_type: 1.0,
            monofunctional_chains_type: 1.0,
        }
    )

    # validation
    if target_p is not None:
        assert math.isclose(
            target_p,
            compute_crosslinker_conversion(
                universe, crosslinker_type=crosslink_type, f=target_f
            ),
            rel_tol=0.05,
        )
    # TODO: also check for w_sol instead

    if n_mono_chains == 0:
        assert math.isclose(
            target_r,
            compute_stoichiometric_imbalance(
                universe,
                crosslinker_type=crosslink_type,
                functionality_per_type={
                    normal_atom_type: 2,
                    crosslink_type: target_f,
                    monofunctional_chains_type: 1,
                },
            ),
            rel_tol=0.05,
        )
    bond_lengths = universe.compute_bond_lengths()
    print(
        "Bond lengths, squared mean: {}, mean: {} (median: {}, max: {}, min: {})".format(
            np.mean(np.square(bond_lengths)),
            np.mean(bond_lengths),
            np.median(bond_lengths),
            max(bond_lengths),
            min(bond_lengths),
        )
    )

    # assert math.isclose(params.get("<b>").magnitude, np.mean(bond_lengths), rel_tol=0.2)
    # assert math.isclose(
    #     mean_squared_bead_distance, np.mean(np.square(bond_lengths)), rel_tol=0.2
    # )

    # end_to_end_distances = universe.compute_end_to_end_distances(
    #     crosslinker_type=crosslink_type, derive_image_flags=True
    # )
    # if n_mono_chains == 0:
    #     assert math.isclose(
    #         np.mean(np.square(end_to_end_distances)),
    #         n_beads_per_chain * mean_squared_bead_distance,
    #         rel_tol=(
    #             0.05
    #             if (
    #                 (target_p is not None and target_p < 0.98)
    #                 or (target_wsol is not None and target_wsol < 0.05)
    #             )
    #             else 0.1
    #         ),
    #     )
    assert math.isclose(
        universe.get_nr_of_atoms() / universe.get_volume(),
        bead_density,
    )

    return universe
