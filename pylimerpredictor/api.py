"""
This file provides three API endpoints:
they all accept a POST request with a JSON payload,
namely the PredictionInput class, which they parse,
and then use to generate a prediction.
"""

import json
import logging
import math
import re

import numpy as np
from django.contrib.auth.decorators import login_required
from django.core.exceptions import BadRequest, ValidationError
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from pylimer_doctorate_utils.polymer_parameter_provider import (
    assemble_parameters_from_kuhn,
)
from quantityfield.units import ureg

from pylimerpredictor.predictors.normal_mode_predictor import (
    predict_normal_mode_results,
)

from .models.prediction_input import PredictionInput
from .predictors.ant_predictor import predict_ant_results
from .predictors.mmt_predictor import predict_mmt_results
from .predictors.nn_predictor import predict_nn_results

logger = logging.getLogger(__name__)


# Utility to get the most suitable content type from the Accept header
def get_accepted_content_types(request):
    def qualify(x):
        parts = x.split(";", 1)
        if len(parts) == 2:
            match = re.match(r"(^|;)q=(0(\.\d{,3})?|1(\.0{,3})?)(;|$)", parts[1])
            if match:
                return parts[0], float(match.group(2))
        return parts[0], 1

    raw_content_types = request.META.get("HTTP_ACCEPT", "*/*").split(",")
    qualified_content_types = map(qualify, raw_content_types)
    return (
        x[0] for x in sorted(qualified_content_types, key=lambda x: x[1], reverse=True)
    )


# Utility to parse the JSON payload and create a PredictionInput object
def parse_prediction_input(request_body):
    try:
        data = json.loads(request_body)
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in request: {e}")
        return None

    # Remove CSRF token if present
    data.pop("csrfmiddlewaretoken", None)

    try:
        # Create instance without saving to database
        prediction_input = PredictionInput(**data)
        # Validate the model fields
        prediction_input.full_clean()
        return prediction_input
    except (TypeError, ValueError, ValidationError) as e:
        logger.warning(f"Invalid prediction input data: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing prediction input: {e}")
        return None


# Decorator to enforce authentication and disable CSRF for simplicity
@csrf_exempt
@login_required
def prediction_endpoint_mmt(request):
    requested_content_types = get_accepted_content_types(request)
    if request.method == "POST":
        prediction_input = parse_prediction_input(request.body)
        if prediction_input:
            prediction = predict_mmt_results(prediction_input)
            if "application/json" in requested_content_types:
                return JsonResponse(prediction, status=200)
            return render(
                request,
                "prediction/mmt_prediction.html",
                context={**prediction, "input": prediction_input},
            )
        raise BadRequest("Invalid input")
    raise BadRequest("Only POST method is allowed")


@csrf_exempt
@login_required
def prediction_endpoint_nn(request):
    requested_content_types = get_accepted_content_types(request)
    if request.method == "POST":
        prediction_input = parse_prediction_input(request.body)
        if prediction_input:
            prediction = predict_nn_results(prediction_input)
            if "application/json" in requested_content_types:
                return JsonResponse(prediction, status=200)
            return render(request, "prediction/nn_prediction.html", context=prediction)
        raise BadRequest("Invalid input")
    raise BadRequest("Only POST method is allowed")


@csrf_exempt
@login_required
def prediction_endpoint_nma(request):
    requested_content_types = get_accepted_content_types(request)
    if request.method == "POST":
        prediction_input = parse_prediction_input(request.body)
        if prediction_input:
            prediction = predict_normal_mode_results(prediction_input)
            for key, value in prediction.items():
                if isinstance(value, np.ndarray):
                    prediction[key] = value.tolist()
            if "application/json" in requested_content_types:
                return JsonResponse(prediction, status=200)
            return render(
                request,
                "prediction/nma_prediction.html",
                context={**prediction, "json_data": json.dumps(prediction)},
            )
        raise BadRequest("Invalid input")
    raise BadRequest("Only POST method is allowed")


@csrf_exempt
@login_required
def prediction_endpoint_ant(request):
    requested_content_types = get_accepted_content_types(request)
    if request.method == "POST":
        prediction_input = parse_prediction_input(request.body)
        if prediction_input:
            prediction = predict_ant_results(prediction_input)
            if "application/json" in requested_content_types:
                return JsonResponse(prediction, status=200)
            return render(request, "prediction/ant_prediction.html", context=prediction)
        logger.warning("Invalid prediction input data", request.body)
        raise BadRequest("Invalid input")
    raise BadRequest("Only POST method is allowed")


@csrf_exempt
@login_required
def polymer_parameters(request):
    """
    Endpoint to retrieve polymer parameters for the prediction form.
    Returns a JSON response with the parameters.
    """
    if request.method == "GET":
        from pylimer_tools.io.unit_styles import UnitStyleFactory

        unit_style_factory = UnitStyleFactory()
        everaers_data = unit_style_factory.get_everares_et_al_data()

        params = {}

        for i, row in everaers_data.iterrows():
            parameters = assemble_parameters_from_kuhn(
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
                "mean_squared_bead_distance": parameters.get("<b^2>")
                .to("nm^2")
                .magnitude,
                "bead_mass": parameters.get("Mw").to("kg/mol").magnitude,
                "entanglement_sampling_cutoff": parameters.get_sampling_cutoff(),
            }

        return JsonResponse(params, status=200)
    raise BadRequest("Only GET method is allowed")
