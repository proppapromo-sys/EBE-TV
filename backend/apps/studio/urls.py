from django.urls import path

from . import views

urlpatterns = [
    path("studio/enable", views.enable),
    path("studio/shows", views.ShowsView.as_view()),
    path("studio/seasons", views.SeasonsView.as_view()),
    path("studio/episodes", views.EpisodesView.as_view()),
    path("studio/videos/upload-url", views.UploadURLView.as_view()),
    path("studio/episodes/<uuid:episode_id>/status", views.episode_status),
    path("studio/submit", views.submit),
]
