from rest_framework import serializers

from apps.analysis.models import AnalysisResult
from apps.companies.models import Company
from apps.market.models import Price
from apps.news.models import Article, ArticleTag


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ("id", "symbol", "name", "sector", "aliases", "active")


class CompanyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ("name", "aliases", "active")


class RangeQuerySerializer(serializers.Serializer):
    range = serializers.ChoiceField(choices=["7d", "30d", "90d"], default="30d")


class PriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Price
        fields = ("date", "open", "high", "low", "close", "volume", "turnover", "trades")


class AnalysisPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisResult
        fields = (
            "date",
            "vwap",
            "close_vs_vwap_pct",
            "pressure",
            "pressure_5d",
            "volume_zscore",
            "is_volume_anomaly",
            "news_count",
            "next_day_return_pct",
            "next_day_volume_change_pct",
            "top_buyers",
            "top_sellers",
        )


class ArticleTagSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source="company.symbol", read_only=True)

    class Meta:
        model = ArticleTag
        fields = ("company", "symbol", "confidence", "source", "matched_on")


class ArticleSerializer(serializers.ModelSerializer):
    tags = ArticleTagSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = ("id", "url", "portal", "title", "body", "raw_date", "published_at", "categorized", "tags")


class RecategorizeSerializer(serializers.Serializer):
    company_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
    )

    def validate_company_ids(self, value):
        unique = list(dict.fromkeys(value))
        found = set(Company.objects.filter(pk__in=unique, active=True).values_list("pk", flat=True))
        missing = [company_id for company_id in unique if company_id not in found]
        if missing:
            raise serializers.ValidationError(f"Unknown company ids: {missing}")
        return unique
