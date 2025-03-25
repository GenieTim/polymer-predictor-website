import math

from django.db import models
from quantityfield.fields import QuantityField
from quantityfield.units import ureg
from pint import Quantity


class PredictionInput(models.Model):
    # Synthesis parameters
    stoichiometric_imbalance = models.FloatField()
    crosslink_conversion = models.FloatField()
    crosslink_functionality = models.IntegerField()

    # Bead quantities
    n_bifunctional_chains = models.IntegerField()
    n_monofunctional_chains = models.IntegerField()
    n_beads_bifunctional = models.IntegerField()
    n_beads_monofunctional = models.IntegerField()

    # Material & measurement properties
    temperature = QuantityField(default_unit="K")
    density = QuantityField(default_unit="kg/cm^3")
    bead_mass = QuantityField(default_unit="kg/mol")
    mean_squared_bead_distance = QuantityField(default_unit="nm^2")
    plateau_modulus = QuantityField(default_unit="MPa")

    # Additional Info
    creator = models.ForeignObject(to="users.User")
    creation_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

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
        return math.sqrt(self.mean_squared_bead_distance / alpha)

    def get_bead_density(self) -> Quantity:
        bead_density = self.density / self.bead_mass
        if bead_density.check("[substance]/[volume]"):
            Na = 6.022e23 * ureg("1/mol")
            bead_density = bead_density * Na
        assert bead_density.check("[volume]^-1")
        return bead_density
