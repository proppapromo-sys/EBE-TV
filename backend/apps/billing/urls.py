from django.urls import path

from . import views

urlpatterns = [
    path("webhooks/stripe", views.stripe_webhook),
    path("webhooks/apple", views.apple_webhook),
    path("webhooks/google", views.google_webhook),
]
