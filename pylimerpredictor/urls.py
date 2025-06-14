"""
URL configuration for pylimerpredictor project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path

from . import api, auth_views, views

urlpatterns = [
    path("", views.home, name="home"),
    path("prediction/", views.prediction, name="prediction"),
    # Authentication URLs
    path("accounts/login/", auth_views.login_view, name="login"),
    path("accounts/register/", auth_views.register_view, name="register"),
    path("accounts/logout/", auth_views.logout_view, name="logout"),
    path("accounts/profile/", auth_views.profile_view, name="profile"),
    # Admin user management
    path("admin/", admin.site.urls),
    path("users-admin/", auth_views.user_management_view, name="user_management"),
    path(
        "users-admin/<int:user_id>/role/",
        auth_views.update_user_role,
        name="update_user_role",
    ),
    path(
        "users-admin/<int:user_id>/toggle/",
        auth_views.toggle_user_active,
        name="toggle_user_active",
    ),
    # API endpoints
    path("api/polymer-parameters/", api.polymer_parameters, name="polymer_parameters"),
    path("api/mmt/", api.prediction_endpoint_mmt, name="mmt_prediction"),
    path("api/nn/", api.prediction_endpoint_nn, name="nn_prediction"),
    path("api/ant/", api.prediction_endpoint_ant, name="ant_prediction"),
    path("api/nma/", api.prediction_endpoint_nma, name="nma_prediction"),
]
