"""
This file provides three API endpoints:
they all accept a POST request with a JSON payload,
namely the PredictionInput class, which they parse,
and then use to generate a prediction.
"""

import concurrent.futures
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

            # add _str keys for formatted values
            for key, value in list(prediction.items()):
                if isinstance(value, (int, float, np.number)):
                    prediction[f"{key}_str"] = format_value(value)

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

            # add _str keys for formatted values
            for key, value in list(prediction.items()):
                if isinstance(value, (int, float, np.number)):
                    prediction[f"{key}_str"] = format_value(value)

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
            # Check if this is a refinement request
            refinement_level = request.GET.get("refinement", "5")
            n_runs = min(int(refinement_level), 10)  # Cap at 10 runs

            if n_runs == 1:
                # Single prediction for fast response
                prediction = predict_ant_results(prediction_input)
            else:
                # Multiple runs for error estimation - run in parallel
                predictions = run_ant_predictions_parallel(prediction_input, n_runs)
                # Calculate means and standard deviations
                prediction = calculate_ant_statistics(predictions)

            if "application/json" in requested_content_types:
                return JsonResponse(prediction, status=200)
            return render(request, "prediction/ant_prediction.html", context=prediction)
        logger.warning("Invalid prediction input data", request.body)
        raise BadRequest("Invalid input")
    raise BadRequest("Only POST method is allowed")


def run_ant_predictions_parallel(prediction_input, n_runs):
    """Run multiple ANT predictions in parallel."""
    with concurrent.futures.ProcessPoolExecutor(max_workers=min(n_runs, 8)) as executor:
        # Submit all prediction tasks
        futures = [
            executor.submit(predict_ant_results, prediction_input)
            for _ in range(n_runs)
        ]

        # Collect results as they complete
        predictions = []
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                predictions.append(result)
            except Exception as e:
                logger.error(f"ANT prediction failed: {e}")
                # Continue with other predictions even if one fails

        return predictions


def format_value(value):
    """
    Formats a numerical value with appropriate decimal precision.

    Args:
        value (float): The numerical value to format.

    Returns:
        str: A string representation of the value rounded to the appropriate number of decimal places.
    """
    if value == 0:
        return "0.00"  # Special case for zero

    return "{:.3g}".format(value)


def format_value_with_error(value, error):
    """
    Formats a numerical value and its associated error with appropriate decimal precision.

    The number of decimal places is determined based on the order of magnitude of the error,
    ensuring both the value and error are displayed with matching precision.

    Args:
        value (float): The numerical value to format.
        error (float): The associated error or uncertainty.

    Returns:
        str: A string representation of the value and error in the format "value ± error",
             with both numbers rounded to the appropriate number of decimal places.

    Example:
        >>> format_value_with_error(12.3456, 0.0789)
        '12.35 ± 0.08'
    """
    # Determine the number of decimal places based on the error
    error_exp = np.floor(np.log10(abs(error)))  # Order of magnitude of the error
    decimals = max(0, -int(error_exp))  # Determine decimal places to keep

    # Format the number and error with the same decimal precision
    formatted_value = f"{round(value, decimals):.{decimals}f}"
    formatted_error = f"{round(error, decimals):.{decimals}f}"

    return f"{formatted_value} ± {formatted_error}"


def calculate_ant_statistics(predictions: list):
    """Calculate mean and standard deviation for ANT predictions."""
    import numpy as np

    keys = [
        "g_ant",
        "g_phantom",
        "g_entangled",
        "w_dangling",
        "w_soluble",
        "w_backbone",
    ]
    if not keys:
        return {}
    assert all(key in pred for pred in predictions for key in keys)
    result = {}

    for key in keys:
        values = [p[key] for p in predictions]
        result[key] = np.mean(values)
        if len(values) > 1:
            # Calculate standard deviation only if we have more than one prediction
            result[f"{key}_error"] = np.std(values, ddof=1)
            # format such that the number of decimals
            # of mean and error are sensible based on the magnitude of the error
            result[f"{key}_str"] = format_value_with_error(
                result[key], result[f"{key}_error"]
            )
        else:
            result[f"{key}_str"] = f"{result[key]:.5f}"

    result["n_runs"] = len(predictions)
    return result


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
