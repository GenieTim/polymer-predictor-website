#!/usr/bin/env python

import json
import os
from pylimer_tools.io.bead_spring_parameter_provider import (
    assemble_gaussian_parameters_from_kuhn,
)
from pylimer_tools.io.unit_styles import UnitStyleFactory

unit_style_factory = UnitStyleFactory()
ureg = unit_style_factory.get_unit_registry()
everaers_data = unit_style_factory.get_everares_et_al_data()

params = {}

for i, row in everaers_data.iterrows():
    parameters = assemble_gaussian_parameters_from_kuhn(
        ureg=ureg,
        kuhn_length=row["l_K"] * ureg("angstrom"),
        kuhn_mass=row["M_k"] * ureg("g/mol"),
        density=row["rho_bulk"] * ureg("g/cm^3"),
        temperature=row["T_ref"] * ureg("K"),
        entanglement_modulus=row["G_e"] * ureg("MPa"),
        name=row["name"].replace("*", "").strip(),
    )

    params[row["name"].replace("*", "").strip()] = {
        "density": parameters.get("density").to("kg/cm^3").magnitude,
        "temperature": row["T_ref"],  # Kelvin
        "plateau_modulus": row["G_e"],  # MPa
        "mean_squared_bead_distance": parameters.get("<b^2>").to("nm^2").magnitude,
        "bead_mass": parameters.get("Mw").to("kg/mol").magnitude,
        "entanglement_sampling_cutoff": parameters.get_sampling_cutoff(),
        "name": row["name"].replace("*", "").strip(),
    }

with open(
    os.path.join(os.path.dirname(__file__), "../src", "polymer-presets.json"), "w"
) as f:
    json.dump(params, f, indent=4)
