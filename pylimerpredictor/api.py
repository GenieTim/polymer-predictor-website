"""
This file provides three API endpoints:
they all accept a POST request with a JSON payload,
namely the PredictionInput class, which they parse,
and then use to generate a prediction.
"""

import json
import re

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from models.prediction_input import PredictionInput
from predictors.mmt_predictor import predict_mmt_results
from django.shortcuts import render
from django.core.exceptions import BadRequest
from predictors.nn_predictor import predict_nn_results


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
        return PredictionInput(data)
    except (json.JSONDecodeError, KeyError):
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
            return render(request, "prediction/mmt_prediction.html", context=prediction)
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
            return render(request, "prediction/mmt_prediction.html", context=prediction)
        raise BadRequest("Invalid input")
    raise BadRequest("Only POST method is allowed")


@csrf_exempt
@login_required
def prediction_endpoint_ant(request):
    requested_content_types = get_accepted_content_types(request)
    if request.method == "POST":
        prediction_input = parse_prediction_input(request.body)
        if prediction_input:
            prediction = generate_prediction(prediction_input)
            if "application/json" in requested_content_types:
                return JsonResponse(prediction, status=200)
            return render(request, "prediction/mmt_prediction.html", context=prediction)
        raise BadRequest("Invalid input")
    raise BadRequest("Only POST method is allowed")
