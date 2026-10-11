from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdminRole
from apps.crawling.models import CrawlRun
from apps.crawling.sync import enqueue_sync
from common.responses import success_response


def _run_payload(run: CrawlRun) -> dict:
    error = (run.error or "")[:400]
    return {
        "id": run.id,
        "kind": run.kind,
        "portal": run.portal,
        "status": run.status,
        "items": run.items,
        "error": error,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
    }


class AdminSyncView(APIView):
    permission_classes = [IsAdminRole]

    @extend_schema(tags=["Admin"], summary="Recent crawl runs")
    def get(self, request):
        runs = CrawlRun.objects.all()[:20]
        return success_response([_run_payload(run) for run in runs])

    @extend_schema(tags=["Admin"], summary="Queue news, prices, and floorsheet now")
    def post(self, request):
        queued = enqueue_sync(user=request.user)
        return success_response(queued, message="Sync queued.")
