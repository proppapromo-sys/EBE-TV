"""Root URL routing — every app mounts under /api."""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(_request):
    return JsonResponse({"ok": True, "service": "streaming-backend"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health", health),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.catalog.urls")),
    path("api/", include("apps.subscriptions.urls")),
    path("api/", include("apps.playback.urls")),
    path("api/", include("apps.billing.urls")),
    path("api/", include("apps.cms.urls")),
    path("api/", include("apps.payouts.urls")),
]
