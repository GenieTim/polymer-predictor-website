from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def home(request):
    render(request, "home.html")


@login_required
def prediction(request):
    # render the django template offering the prediction form
    return render(request, "prediction_form.html")
