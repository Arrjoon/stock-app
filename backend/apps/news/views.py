from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.views import APIView

from apps.accounts.permissions import IsAnalystOrAdmin, IsViewerOrAbove
from apps.companies.serializers import ArticleSerializer, RecategorizeSerializer
from apps.news.models import Article, ArticleTag, TagCorrection
from common.responses import success_response


class NewsListView(APIView):
    permission_classes = [IsViewerOrAbove]

    @extend_schema(
        tags=["News"],
        summary="Categorized news",
        parameters=[
            OpenApiParameter(name="company_id", type=int, location=OpenApiParameter.QUERY, required=False),
        ],
        responses=ArticleSerializer(many=True),
    )
    def get(self, request):
        articles = Article.objects.prefetch_related("tags__company").order_by("-published_at", "-crawled_at")
        company_id = request.query_params.get("company_id")
        if company_id:
            if not str(company_id).isdigit():
                raise ValidationError({"company_id": "Must be an integer."})
            articles = articles.filter(tags__company_id=int(company_id)).distinct()
        return success_response(ArticleSerializer(articles[:40], many=True).data)


class RecategorizeView(APIView):
    permission_classes = [IsAnalystOrAdmin]

    @extend_schema(tags=["News"], summary="Replace article tags", request=RecategorizeSerializer)
    def post(self, request, pk):
        article = Article.objects.filter(pk=pk).first()
        if article is None:
            raise NotFound("Article not found.")
        serializer = RecategorizeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company_ids = serializer.validated_data["company_ids"]
        old_tags = list(article.tags.values("company_id", "confidence", "source", "matched_on"))
        article.tags.all().delete()
        new_tags = []
        for company_id in company_ids:
            tag = ArticleTag.objects.create(
                article=article,
                company_id=company_id,
                confidence=1.0,
                source=ArticleTag.Source.MANUAL,
                matched_on=[{"kind": "manual"}],
            )
            new_tags.append(
                {"company_id": tag.company_id, "confidence": tag.confidence, "source": tag.source}
            )
        TagCorrection.objects.create(
            article=article,
            old_tags=old_tags,
            new_tags=new_tags,
            user=request.user,
        )
        article.categorized = True
        article.save(update_fields=["categorized"])
        return success_response(ArticleSerializer(article).data, message="Tags updated.")
