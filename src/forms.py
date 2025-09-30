from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.safestring import mark_safe

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """Custom user registration form"""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Enter your email address"}
        ),
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "First name"}
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Last name"}
        ),
    )
    institution = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Institution (optional)"}
        ),
    )

    class Meta:
        model = User
        fields = (
            "email",
            "username",
            "first_name",
            "last_name",
            "institution",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style the form fields
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Choose a username"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Enter password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Confirm password"}
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.institution = self.cleaned_data["institution"]
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """Custom login form"""

    username = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your email address",
                "autofocus": True,
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Enter your password"}
        )
    )


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile"""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "institution"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "institution": forms.TextInput(attrs={"class": "form-control"}),
        }


class PolymerPredictionForm(forms.Form):
    label_suffix = ""

    default_mw = 0.262525

    # Polymer properties (disabled fields)
    polymer_name = forms.CharField(
        initial="PDMS",
        widget=forms.TextInput(attrs={"class": "form-control", "readonly": True}),
    )
    temperature = forms.FloatField(
        initial=293.15,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "readonly": True}),
    )
    density = forms.FloatField(
        initial=0.965,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "readonly": True}),
    )
    plateau_modulus = forms.FloatField(
        initial=0.2,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "readonly": True}),
    )
    bead_mass = forms.FloatField(
        initial=default_mw,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "readonly": True}),
    )
    mean_squared_bead_distance = forms.FloatField(
        initial=1.10700879,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "readonly": True}),
    )

    # Network parameters (editable fields)
    stoichiometric_imbalance = forms.FloatField(
        initial=1.0,
        min_value=0.5,
        max_value=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    crosslink_functionality = forms.IntegerField(
        initial=4,
        min_value=3,
        max_value=6,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    crosslink_conversion = forms.FloatField(
        initial=0.95,
        min_value=0,
        max_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    # Replace chain number inputs with b2 fraction
    b2_molar_fraction = forms.FloatField(
        initial=1.0,
        min_value=0.0,
        max_value=1.0,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    mw_bifunctional = forms.FloatField(
        initial=30 * default_mw,
        min_value=0.1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    mw_monofunctional = forms.FloatField(
        initial=0,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    mw_xlinks = forms.FloatField(
        initial=1 * default_mw,
        min_value=0.1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    # Additional synthesis parameters
    extract_solvent_before_measurement = forms.BooleanField(
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    disable_primary_loops = forms.BooleanField(
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    disable_secondary_loops = forms.BooleanField(
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    functionalize_discrete = forms.BooleanField(
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    # Zero-functional chains (hidden - set to 0)
    n_zerofunctional_chains = forms.IntegerField(
        initial=0,
        min_value=0,
        max_value=10000,
        widget=forms.HiddenInput(),
    )
    mw_zerofunctional = forms.FloatField(
        initial=0,
        min_value=0,
        widget=forms.HiddenInput(),
    )

    # Additional material property
    entanglement_sampling_cutoff = forms.FloatField(
        initial=2.5,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.1"}),
    )

    # Metadata fields
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Optional description",
            }
        ),
    )

    def make_label_str(self, description: str, symbol: str = "", unit: str = "") -> str:
        """
        Create a label string with proper formatting.
        :param description: Description of the field.
        :param symbol: Symbol to be included in the label.
        :param unit: Unit to be included in the label.
        :return: Formatted label string.
        """
        if symbol and unit:
            return mark_safe(f"<i>{symbol}</i> [{unit}] ({description})")
        if symbol:
            return mark_safe(f"<i>{symbol}</i> ({description})")
        if unit:
            return mark_safe(f"{description} [{unit}]")
        return mark_safe(description)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        # Add labels with proper formatting
        self.fields["temperature"].label = self.make_label_str("Temperature", "T", "K")
        self.fields["density"].label = self.make_label_str("Density", "ρ", "kg/cm³")
        self.fields["plateau_modulus"].label = self.make_label_str(
            "Entanglement modulus", "G<sub>e</sub>(1)", "MPa"
        )
        self.fields["bead_mass"].label = self.make_label_str(
            "Bead mass", "M<sub>w</sub>", "kg/mol"
        )
        self.fields["mean_squared_bead_distance"].label = self.make_label_str(
            "Mean squared bead distance", "⟨b<sup>2</sup>⟩", "nm²"
        )
        self.fields["stoichiometric_imbalance"].label = self.make_label_str(
            "Stoichiometric imbalance", "r"
        )
        self.fields["crosslink_functionality"].label = self.make_label_str(
            "Cross-link functionality", "f"
        )
        self.fields["crosslink_conversion"].label = self.make_label_str(
            "Cross-link conversion", "p"
        )
        self.fields["b2_molar_fraction"].label = self.make_label_str(
            "molar fraction of 2×B<sub>2</sub> in B<sub>1</sub> + 2×B<sub>2</sub>",
            "b<sub>2</sub>",
        )
        self.fields["mw_bifunctional"].label = self.make_label_str(
            "Molecular weight per bifunctional chain",
            "M<sub>w</sub><sup>B<sub>2</sub></sup>",
            "kg/mol",
        )
        self.fields["mw_monofunctional"].label = self.make_label_str(
            "Molecular weight per monofunctional chain",
            "M<sub>w</sub><sup>B<sub>1</sub></sup>",
            "kg/mol",
        )
        self.fields["mw_xlinks"].label = self.make_label_str(
            "Molecular weight per cross-link", "M<sub>w</sub><sup>X</sup>", "kg/mol"
        )
        self.fields["entanglement_sampling_cutoff"].label = self.make_label_str(
            "Entanglement sampling cutoff", "s<sub>c</sub>", "nm"
        )
        self.fields["extract_solvent_before_measurement"].label = self.make_label_str(
            "Extract solvent before measurement"
        )
        self.fields["disable_primary_loops"].label = self.make_label_str(
            "Disable primary loops"
        )
        self.fields["disable_secondary_loops"].label = self.make_label_str(
            "Disable secondary loops"
        )
        self.fields["functionalize_discrete"].label = self.make_label_str(
            "Functionalize discrete"
        )
        self.fields["description"].label = self.make_label_str("Description")
