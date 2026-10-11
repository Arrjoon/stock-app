from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.permissions import HasRole
from apps.accounts.serializers import UserCreateSerializer, UserSerializer, UserUpdateSerializer
from common.responses import success_response


class MeView(APIView):
    @extend_schema(tags=["Auth"], summary="Current user", responses=UserSerializer)
    def get(self, request):
        return success_response(UserSerializer(request.user).data)


class UserListCreateView(APIView):
    permission_classes = [HasRole]
    required_roles = [User.Role.ADMIN]

    @extend_schema(tags=["Admin"], summary="List users", responses=UserSerializer(many=True))
    def get(self, request):
        users = User.objects.order_by("email")
        return success_response(UserSerializer(users, many=True).data)

    @extend_schema(tags=["Admin"], summary="Create a user", request=UserCreateSerializer, responses=UserSerializer)
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return success_response(UserSerializer(user).data, status_code=201)


class UserDetailView(APIView):
    permission_classes = [HasRole]
    required_roles = [User.Role.ADMIN]

    @extend_schema(tags=["Admin"], summary="Change role or deactivate", request=UserUpdateSerializer, responses=UserSerializer)
    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        serializer = UserUpdateSerializer(user, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(UserSerializer(user).data)
