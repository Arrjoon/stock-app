"""OpenAPI helpers so Swagger shows the success and error envelopes."""

from drf_spectacular.utils import OpenApiResponse, inline_serializer
from rest_framework import serializers


class ErrorDetailSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.JSONField(required=False, allow_null=True)


class ErrorEnvelopeSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    error = ErrorDetailSerializer()


def enveloped(name, data_field):
    """Wrap a data serializer in `{ success, message, data }`."""
    return inline_serializer(
        name=name,
        fields={
            "success": serializers.BooleanField(),
            "message": serializers.CharField(),
            "data": data_field,
        },
    )


ERROR_RESPONSE = OpenApiResponse(
    response=ErrorEnvelopeSerializer,
    description="Error envelope. The body has no stack trace.",
)
