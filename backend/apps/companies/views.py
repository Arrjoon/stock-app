import csv
from datetime import timedelta

from django.http import HttpResponse
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.permissions import HasRole, IsViewerOrAbove
from apps.analysis.models import AnalysisResult
from apps.companies.models import Company
from apps.companies.selectors import comparison, get_active_company, parse_range_days
from apps.companies.serializers import (
    AnalysisPointSerializer,
    CompanySerializer,
    CompanyUpdateSerializer,
    PriceSerializer,
    RangeQuerySerializer,
)
from apps.market.models import Price
from apps.news.models import Article
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
        rows = CompanySerializer(Company.objects.filter(active=True), many=True).data
        for row in rows:
            closes = list(
                Price.objects.filter(company_id=row["id"]).order_by("-date").values_list("close", flat=True)[:2]
            )
            row["last_close"] = closes[0] if closes else None
            row["prev_close"] = closes[1] if len(closes) > 1 else None
        return success_response(rows)


class CompanyDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "PATCH":
            self.required_roles = [User.Role.ADMIN]
            return [HasRole()]
        return [IsViewerOrAbove()]

    @extend_schema(tags=["Companies"], summary="One company", responses=CompanySerializer)
    def get(self, request, key):
        return success_response(CompanySerializer(get_active_company(key)).data)

    @extend_schema(tags=["Admin"], summary="Update watchlist fields", request=CompanyUpdateSerializer, responses=CompanySerializer)
    def patch(self, request, key):
        company = Company.objects.filter(pk=int(key)).first() if str(key).isdigit() else None
        if company is None:
            company = Company.objects.filter(symbol__iexact=key).first()
        if company is None:
            from rest_framework.exceptions import NotFound

            raise NotFound("Company not found.")
        serializer = CompanyUpdateSerializer(company, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(CompanySerializer(company).data)


class CompanyPricesView(APIView):
    permission_classes = [IsViewerOrAbove]

    @extend_schema(tags=["Market"], summary="Daily OHLCV", parameters=[RANGE_PARAM], responses=PriceSerializer(many=True))
    def get(self, request, key):
        company = get_active_company(key)
        query = RangeQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        days = parse_range_days(query.validated_data["range"])
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


class CompanyBehaviorSummaryView(APIView):
    permission_classes = [IsViewerOrAbove]

    @extend_schema(tags=["Analysis"], summary="Behavior summary", parameters=[RANGE_PARAM])
    def get(self, request, key):
        company = get_active_company(key)
        days = parse_range_days(request.query_params.get("range"))
        since = timezone.localdate() - timedelta(days=days)
        points = list(
            AnalysisResult.objects.filter(company=company, date__gte=since).order_by("date")
        )
        serialized = AnalysisPointSerializer(points, many=True).data
        latest = serialized[-1] if serialized else None
        pressure = latest["pressure"] if latest else None
        if pressure is None:
            label = "unknown"
        elif pressure > 0:
            label = "buy"
        elif pressure < 0:
            label = "sell"
        else:
            label = "neutral"
        return success_response(
            {
                "latest": latest,
                "pressure_label": label,
                "anomaly": {
                    "flag": bool(latest and latest["is_volume_anomaly"]),
                    "method": "20-day rolling volume z-score",
                    "threshold": 2.5,
                    "volume_zscore": latest["volume_zscore"] if latest else None,
                },
                "chart": serialized,
            }
        )


class CompanyExportView(APIView):
    permission_classes = [HasRole]
    required_roles = [User.Role.ADMIN, User.Role.ANALYST]

    @extend_schema(tags=["Analysis"], summary="Export prices, analysis, and tagged news")
    def get(self, request, key):
        company = get_active_company(key)
        export_format = (request.query_params.get("format") or "json").lower()
        if export_format not in {"json", "csv"}:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"format": "Use csv or json."})
        prices = PriceSerializer(
            Price.objects.filter(company=company).order_by("date"),
            many=True,
        ).data
        analysis = AnalysisPointSerializer(
            AnalysisResult.objects.filter(company=company).order_by("date"),
            many=True,
        ).data
        articles = [
            {"id": article.id, "title": article.title, "url": article.url, "published_at": article.published_at}
            for article in Article.objects.filter(tags__company=company).distinct().order_by("-published_at")[:100]
        ]
        if export_format == "json":
            return success_response({"company": CompanySerializer(company).data, "prices": prices, "analysis": analysis, "news": articles})
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{company.symbol}.csv"'
        writer = csv.writer(response)
        writer.writerow(["section", "date", "open", "high", "low", "close", "volume", "vwap", "pressure", "anomaly", "title"])
        for row in prices:
            writer.writerow(["price", row["date"], row["open"], row["high"], row["low"], row["close"], row["volume"], "", "", "", ""])
        for row in analysis:
            writer.writerow(["analysis", row["date"], "", "", "", "", "", row["vwap"], row["pressure"], row["is_volume_anomaly"], ""])
        for row in articles:
            writer.writerow(["news", "", "", "", "", "", "", "", "", "", row["title"]])
        return response


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
