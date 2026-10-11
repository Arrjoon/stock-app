from django.urls import path

from apps.accounts.views import UserDetailView, UserListCreateView

urlpatterns = [
    path("", UserListCreateView.as_view(), name="admin-users"),
    path("<int:pk>/", UserDetailView.as_view(), name="admin-user-detail"),
]
