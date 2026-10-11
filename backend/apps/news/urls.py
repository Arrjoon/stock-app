from django.urls import path

from apps.news.views import NewsListView, RecategorizeView

urlpatterns = [
    path("", NewsListView.as_view(), name="news-list"),
    path("<int:pk>/recategorize/", RecategorizeView.as_view(), name="news-recategorize"),
]
