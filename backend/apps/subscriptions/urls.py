from django.urls import path

from . import views

urlpatterns = [
    path("plans", views.PlansView.as_view()),
    path("me/subscription", views.MySubscriptionView.as_view()),
    path("subscribe/stripe", views.SubscribeStripeView.as_view()),
    path("subscribe/verify-iap", views.VerifyIAPView.as_view()),
]
