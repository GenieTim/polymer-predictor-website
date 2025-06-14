from django.shortcuts import render

from .decorators import researcher_required
from .forms import PolymerPredictionForm


def home(request):
    return render(request, "home.html")


@researcher_required
def prediction(request):
    # render the django template offering the prediction form
    # Only researchers and admins can access prediction functionality
    form = PolymerPredictionForm()
    return render(request, "prediction_form.html", {"form": form})
