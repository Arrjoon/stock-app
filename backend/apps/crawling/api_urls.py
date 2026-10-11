from django.urls import path

from apps.crawling.api_views import CrawlRunListCreateView
from apps.crawling.views import AdminSyncView

urlpatterns = [
    path("sync/", AdminSyncView.as_view(), name="admin-sync"),
    path("crawl-runs/", CrawlRunListCreateView.as_view(), name="admin-crawl-runs"),
]
