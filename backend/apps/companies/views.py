from datetime import timedelta

from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.views import APIView

from apps.accounts.permissions import IsViewerOrAbove
from apps.analysis.models import AnalysisResult
from apps.companies.models import Company
from apps.companies.selectors import comparison, get_active_company, parse_range_days
from apps.companies.serializers import AnalysisPointSerializer, CompanySerializer, PriceSerializer
from apps.market.models import Price
from common.responses import success_response

RANGE_PARAM = OpenApiParameter(
    name="range",
    type=str,
    location=OpenApiParameter.QUERY,
    description="Lookback window: 7d, 30d, or 90d.",
    required=False,
)


class CompanyListView(APIView):
    permission_classes = [IsViewerOrAbove]

    @extend_schema(tags=["Companies"], summary="Active watchlist", responses=CompanySerializer(many=True))
    def get(self, request):
        companies = CompanySerializer(Company.objects.filter(active=True), many=True)
        return success_response(companies.data)


class CompanyDetailView(APIView):
    permission_classes = [IsViewerOrAbove]

    @extend_schema(tags=["Companies"], summary="One company", responses=CompanySerializer)
    def get(self, request, key):
        return success_response(CompanySerializer(get_active_company(key)).data)


class CompanyPricesView(APIView):
    permission_classes = [IsViewerOrAbove]

    @extend_schema(tags=["Market"], summary="Daily OHLCV", parameters=[RANGE_PARAM], responses=PriceSerializer(many=True))
    def get(self, request, key):
        company = get_active_company(key)
        days = parse_range_days(request.query_params.get("range"))
        since = timezone.localdate() - timedelta(days=days)
        prices = Price.objects.filter(company=company, date__gte=since).order_by("date")
        return success_response(PriceSerializer(prices, many=True).data)


class CompanyBehaviorView(APIView):
    permission_classes = [IsViewerOrAbove]

    @extend_schema(
        tags=["Analysis"],
        summary="VWAP, pressure, anomalies, and broker ranks",
        parameters=[RANGE_PARAM],
    )
    def get(self, request, key):
        company = get_active_company(key)
        days = parse_range_days(request.query_params.get("range"))
        since = timezone.localdate() - timedelta(days=days)
        points = AnalysisResult.objects.filter(company=company, date__gte=since).order_by("date")
        serialized = AnalysisPointSerializer(points, many=True).data
        return success_response({"latest": serialized[-1] if serialized else None, "points": serialized})


class CompareView(APIView):
    permission_classes = [IsViewerOrAbove]

    @extend_schema(
        tags=["Analysis"],
        summary="Most volatile, most active, and most in the news",
        parameters=[RANGE_PARAM],
    )
    def get(self, request):
        days = parse_range_days(request.query_params.get("range"))
        return success_response(comparison(days))
