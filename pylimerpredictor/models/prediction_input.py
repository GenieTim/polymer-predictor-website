import math

from django.conf import settings
from django.db import models
from pint import Quantity
from quantityfield.fields import QuantityField
from quantityfield.units import ureg


class PredictionInput(models.Model):
    # Synthesis parameters
    stoichiometric_imbalance = models.FloatField()
    crosslink_conversion = models.FloatField()
    crosslink_functionality = models.IntegerField()

    extract_solvent_before_measurement = models.BooleanField(default=False)
    disable_primary_loops = models.BooleanField(default=False)
    disable_secondary_loops = models.BooleanField(default=False)
    functionalize_discrete = models.BooleanField(default=False)

    # Bead quantities
    n_zerofunctional_chains = models.IntegerField()
    n_monofunctional_chains = models.IntegerField()
    n_bifunctional_chains = models.IntegerField()
    n_beads_zerofunctional = models.IntegerField()
    n_beads_monofunctional = models.IntegerField()
    n_beads_bifunctional = models.IntegerField()
    n_beads_xlinks = models.IntegerField(default=1)

    # Material & measurement properties
    temperature = QuantityField(base_units="K")
    density = QuantityField(base_units="kg/cm^3")
    bead_mass = QuantityField(base_units="kg/mol")
    mean_squared_bead_distance = QuantityField(base_units="nm^2")
    plateau_modulus = QuantityField(base_units="MPa")
    entanglement_sampling_cutoff = QuantityField(base_units="nm")

    # Additional Info
    creator = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who created this prediction",
    )
    creation_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    polymer_name = models.TextField(
        blank=True,
        help_text="Name of the polymer for which the prediction is made",
    )

    # Computed values
    def get_b2(self) -> float:
        return (self.n_bifunctional_chains * 2) / (
            self.n_bifunctional_chains * 2 + self.n_monofunctional_chains
        )

    def get_n_total_chains(self) -> int:
        return self.n_bifunctional_chains + self.n_monofunctional_chains

    def get_n_total_beads(self) -> int:
        return (
            self.n_beads_bifunctional * self.n_bifunctional_chains
            + self.n_beads_monofunctional * self.n_monofunctional_chains
        )

    def get_mean_bead_distance(self) -> Quantity:
        alpha = 3 * math.pi / 8.0
        return math.sqrt(
            self.mean_squared_bead_distance.to("nm^2").magnitude / alpha
        ) * ureg("nm")

    def get_bead_density(self) -> Quantity:
        bead_density = self.density / self.bead_mass
        if bead_density.check("[substance]/[volume]"):
            Na = 6.022e23 * ureg("1/mol")
            bead_density = bead_density * Na
        assert bead_density.check("[volume]^-1")
        return bead_density

    def get_n_chains_crosslinks(self) -> int:
        """
        Infer the number of crosslinks based on the stoichiometric imbalance and
        the number of bifunctional chains.
        """
        if self.stoichiometric_imbalance <= 0:
            return 0
        n_crosslinks = int(
            (
                (self.n_bifunctional_chains * 2 + self.n_monofunctional_chains)
                * self.stoichiometric_imbalance
            )
            / (self.crosslink_functionality)
        )
        return n_crosslinks

    def get_n_beads_total(self) -> int:
        """
        Get the total number of beads in the network.
        """
        return (
            self.n_beads_bifunctional * self.n_bifunctional_chains
            + self.n_beads_monofunctional * self.n_monofunctional_chains
            + self.n_beads_zerofunctional * self.n_zerofunctional_chains
            + self.n_beads_xlinks * self.get_n_chains_crosslinks()
        )

    def get_total_n_beads_solvent(self) -> int:
        """
        Get the number of solvent beads in the network.
        """
        return self.n_beads_zerofunctional * self.n_zerofunctional_chains

    def get_total_n_beads_bifunctional(self) -> int:
        """
        Get the number of bifunctional beads in the network.
        """
        return self.n_beads_bifunctional * self.n_bifunctional_chains

    def get_total_n_beads_monofunctional(self) -> int:
        """
        Get the number of monofunctional beads in the network.
        """
        return self.n_beads_monofunctional * self.n_monofunctional_chains

    def get_total_n_beads_xlinks(self) -> int:
        """
        Get the number of crosslink beads in the network.
        """
        return self.n_beads_xlinks * self.get_n_chains_crosslinks()

    def is_mmtable(self) -> bool:
        """
        Check if the prediction input is suitable for MMTAB prediction.
        """
        return not (
            self.extract_solvent_before_measurement
            or self.n_zerofunctional_chains > 0
            or self.n_beads_xlinks > 1
        )
