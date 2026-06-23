from django.urls import path

from . import views

urlpatterns = [
    path("cms/videos/upload-url", views.UploadURLView.as_view()),
    path("cms/shows", views.ShowsView.as_view()),
    path("cms/episodes", views.EpisodesView.as_view()),
    path("cms/publish", views.PublishView.as_view()),
    path("webhooks/cloudflare", views.cf_transcode_webhook),
]
