from django.urls import path

from . import views

urlpatterns = [
    path("home", views.HomeView.as_view()),
    path("search", views.SearchView.as_view()),
    path("catalog", views.CatalogView.as_view()),
    path("shows/<slug:slug>", views.ShowDetailView.as_view()),
    path("episodes/<uuid:episode_id>", views.EpisodeDetailView.as_view()),
]
