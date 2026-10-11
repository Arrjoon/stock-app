from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "username", "role", "is_active")
        read_only_fields = ("id", "email", "username")


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "username", "password", "role")
        read_only_fields = ("id",)

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("role", "is_active")

    def validate(self, attrs):
        request = self.context["request"]
        if self.instance.pk != request.user.pk:
            return attrs
        if attrs.get("role") not in (None, User.Role.ADMIN):
            raise serializers.ValidationError({"role": "You cannot remove your own admin role."})
        if attrs.get("is_active") is False:
            raise serializers.ValidationError({"is_active": "You cannot deactivate yourself."})
        return attrs
