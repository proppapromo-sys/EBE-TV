from django.urls import path

from . import views

urlpatterns = [
    path("play/<uuid:episode_id>", views.PlayView.as_view()),
    path("progress/<uuid:episode_id>", views.ProgressView.as_view()),
]
