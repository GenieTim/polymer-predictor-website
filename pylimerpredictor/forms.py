from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

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
        initial=0.262525018,
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
    n_bifunctional_chains = forms.IntegerField(
        initial=1000,
        min_value=0,
        max_value=10000,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    n_monofunctional_chains = forms.IntegerField(
        initial=0,
        min_value=0,
        max_value=10000,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    n_beads_bifunctional = forms.IntegerField(
        initial=30,
        min_value=1,
        max_value=500,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    n_beads_monofunctional = forms.IntegerField(
        initial=0,
        min_value=0,
        max_value=500,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    n_beads_xlinks = forms.IntegerField(
        initial=1,
        min_value=1,
        max_value=500,
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

    # Zero-functional chains
    n_zerofunctional_chains = forms.IntegerField(
        initial=0,
        min_value=0,
        max_value=10000,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    n_beads_zerofunctional = forms.IntegerField(
        initial=0,
        min_value=0,
        max_value=500,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
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

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        # Add labels with proper formatting
        self.fields["temperature"].label = "Temperature [K]"
        self.fields["density"].label = "Density [kg/cm³]"
        self.fields["plateau_modulus"].label = "Entanglement modulus Gₑ(1) [MPa]"
        self.fields["bead_mass"].label = "Bead mass [kg/mol]"
        self.fields["mean_squared_bead_distance"].label = (
            "Mean squared bead distance ⟨b²⟩ [nm²]"
        )
        self.fields["stoichiometric_imbalance"].label = "Stoichiometric imbalance r"
        self.fields["crosslink_functionality"].label = "Cross-link functionality f"
        self.fields["crosslink_conversion"].label = "Cross-link conversion p"
        self.fields["n_bifunctional_chains"].label = "Number of bifunctional chains"
        self.fields["n_monofunctional_chains"].label = "Number of monofunctional chains"
        self.fields["n_zerofunctional_chains"].label = (
            "Number of zero-functional chains"
        )
        self.fields["n_beads_bifunctional"].label = "Beads per bifunctional chain"
        self.fields["n_beads_monofunctional"].label = "Beads per monofunctional chain"
        self.fields["n_beads_zerofunctional"].label = "Beads per zero-functional chain"
        self.fields["n_beads_xlinks"].label = "Beads per cross-link"
        self.fields["entanglement_sampling_cutoff"].label = (
            "Entanglement sampling cutoff [nm]"
        )
        self.fields["extract_solvent_before_measurement"].label = (
            "Extract solvent before measurement"
        )
        self.fields["disable_primary_loops"].label = "Disable primary loops"
        self.fields["disable_secondary_loops"].label = "Disable secondary loops"
        self.fields["functionalize_discrete"].label = "Functionalize discrete"
        self.fields["description"].label = "Description"
