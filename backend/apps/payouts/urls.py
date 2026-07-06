from django.urls import path

from . import views

urlpatterns = [
    path("creator/onboard", views.onboard),
    path("creator/account", views.account),
    path("creator/earnings", views.earnings),
]
