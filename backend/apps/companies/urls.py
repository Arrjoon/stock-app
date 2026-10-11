from django.urls import path

from apps.companies.views import (
    CompanyBehaviorView,
    CompanyDetailView,
    CompanyListView,
    CompanyPricesView,
)

urlpatterns = [
    path("", CompanyListView.as_view(), name="company-list"),
    path("<str:key>/", CompanyDetailView.as_view(), name="company-detail"),
    path("<str:key>/prices/", CompanyPricesView.as_view(), name="company-prices"),
    path("<str:key>/behavior/", CompanyBehaviorView.as_view(), name="company-behavior"),
]
