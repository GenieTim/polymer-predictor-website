"""
The shared info regarding which columns and data files to read and fit
"""

import pandas as pd

pdms_only = False
possibly_remove_wsol = False

output_axes = [
    "G [MPa] from gamma Mean, Entangled FB No Slipping",
    "Phantom, FB/FR, G_ANT [MPa]",
    "dangling_fraction Mean, Entangled FB No Slipping",
    "soluble_fraction Mean, Entangled FB No Slipping",
]

output_axes_labels = [
    "G [MPa]",
    "G [MPa], phantom",
    "Dangling weight fraction",
    "Soluble weight fraction",
]

# file_id = "data-anypolymer-mean-filtered-5"
file_id = "combined_data_with_loops_5filtered_mean"
input_axes = (
    [
        "r",
        "p",
        "b2",
        "ge_1 [MPa]",
        "temperature [K]",
        "density [g/cm^3]",
        "param's <b> [nm]",
        # "param's <b^2> [nm^2]",
        "remove_wsol",
        "param's Mw [kg/mol]",
        "Mw [kg/mol]",
        "Mw [kg/mol] monofunctional chains",
        "Mw [kg/mol] solvent chains",
        "Mw [kg/mol] xlink chains",
        "functionality_per_xlink_chain",
        "functionalize_discrete",
        "solvent_fraction_of_beads",
        "monofunctional_fraction_of_beads",  # "b2",
        "bifunctional_fraction_of_beads",
        "entanglement_sampling_cutoff [nm]",
    ]
    if not pdms_only
    else [
        "r",
        "p",
        # "p_relative",
        "b2",
        "ge_1 [MPa]",
        "temperature [K]",
        "density [g/cm^3]",
        "Mw [kg/mol]",
        "Mw [kg/mol] monofunctional chains",
        "Mw [kg/mol] xlink chains",
        "functionality_per_xlink_chain",
        "entanglement_sampling_cutoff [nm]",
        "functionalize_discrete",
        "remove_wsol",
    ]
)

if not possibly_remove_wsol:
    input_axes.remove("remove_wsol")

fit_key = (
    file_id.replace("-mean-filtered-5", "").removesuffix("data-")
    + "_"
    + (
        output_axes[0].replace("[MPa]", "").replace(",", "").strip().replace(" ", "_")
        if len(output_axes) == 1
        else "{}_output_axes".format(len(output_axes))
    )
    + ("-pdms" if pdms_only else "-anypolymer")
    + ("-var-rm-wsol" if possibly_remove_wsol else "")
)


def filter_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    Remove some rows that are outside the scope of the current training
    """
    if pdms_only:
        data = data[
            (data["entanglement_sampling_cutoff [nm]"] >= 2.45)
            & (data["entanglement_sampling_cutoff [nm]"] < 2.7)
        ]
        data = data[(data["temperature [K]"] >= 273) & (data["temperature [K]"] < 300)]
        data = data[data["solvent_fraction_of_beads"] <= 1e-5]
        data = data[(data["params"] == "own-si") | (data["params"] == "si-PDMS*")]
    if not possibly_remove_wsol:
        data = data[data["remove_wsol"] == False]

    # data = data[(data["functionality_per_xlink_chain"] < 100)]
    # data = data[(data["functionalize_discrete"] == True)]
    data = data[((data["r"] <= 2.0) & (data["r"] >= 0.5))]
    # # data = data[data["n_beads_xlinks"] == 1]

    return data
