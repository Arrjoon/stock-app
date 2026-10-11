from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.permissions import HasRole
from apps.crawling.models import CrawlRun
from apps.market.tasks import crawl_floorsheet, crawl_prices
from apps.news.tasks import crawl_portal_news
from apps.realtime.notify import notify
from common.responses import success_response

NEWS_PORTALS = ("merolagani", "sharesansar", "bizmandu")


class CrawlRunSerializer(serializers.ModelSerializer):
    triggered_by = serializers.EmailField(source="triggered_by.email", read_only=True, allow_null=True)

    class Meta:
        model = CrawlRun
        fields = (
            "id",
            "kind",
            "portal",
            "status",
            "items",
            "error",
            "started_at",
            "finished_at",
            "triggered_by",
            "celery_task_id",
        )


class CrawlRunCreateSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=CrawlRun.Kind.choices)
    portal = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        kind = attrs["kind"]
        portal = (attrs.get("portal") or "").strip().lower()
        if kind == CrawlRun.Kind.NEWS:
            if portal not in NEWS_PORTALS:
                raise serializers.ValidationError({"portal": "Use merolagani, sharesansar, or bizmandu."})
        else:
            portal = "nepse"
        attrs["portal"] = portal
        return attrs


class CrawlRunListCreateView(APIView):
    permission_classes = [HasRole]
    required_roles = [User.Role.ADMIN]

    @extend_schema(tags=["Admin"], summary="Recent crawl runs", responses=CrawlRunSerializer(many=True))
    def get(self, request):
        runs = CrawlRun.objects.select_related("triggered_by").order_by("-started_at")[:40]
        return success_response(CrawlRunSerializer(runs, many=True).data)

    @extend_schema(tags=["Admin"], summary="Queue a crawl", request=CrawlRunCreateSerializer, responses=CrawlRunSerializer)
    def post(self, request):
        serializer = CrawlRunCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        kind = serializer.validated_data["kind"]
        portal = serializer.validated_data["portal"]
        run = CrawlRun.objects.create(
            kind=kind,
            portal=portal,
            status=CrawlRun.Status.QUEUED,
            triggered_by=request.user,
        )
        if kind == CrawlRun.Kind.NEWS:
            result = crawl_portal_news.delay(portal, run.id)
        elif kind == CrawlRun.Kind.PRICES:
            result = crawl_prices.delay(run.id)
        else:
            result = crawl_floorsheet.delay(run.id)
        run.celery_task_id = result.id or ""
        run.save(update_fields=["celery_task_id"])
        notify("crawl", run_id=run.id, kind=kind, status=run.status)
        return success_response(CrawlRunSerializer(run).data, message="Crawl queued.", status_code=202)
