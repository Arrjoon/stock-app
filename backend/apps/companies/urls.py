from django.urls import path

from apps.companies.views import (
    CompanyBehaviorSummaryView,
    CompanyBehaviorView,
    CompanyDetailView,
    CompanyExportView,
    CompanyListView,
    CompanyPricesView,
)

urlpatterns = [
    path("", CompanyListView.as_view(), name="company-list"),
    path("<str:key>/", CompanyDetailView.as_view(), name="company-detail"),
    path("<str:key>/prices/", CompanyPricesView.as_view(), name="company-prices"),
    path("<str:key>/behavior/", CompanyBehaviorView.as_view(), name="company-behavior"),
    path("<str:key>/behaviorsummary/", CompanyBehaviorSummaryView.as_view(), name="company-behavior-summary"),
    path("<str:key>/export/", CompanyExportView.as_view(), name="company-export"),
]
