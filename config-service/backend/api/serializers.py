from rest_framework import serializers

from api.models import Application, Configuration, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ApplicationSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), required=False
    )

    class Meta:
        model = Application
        fields = [
            "id",
            "name",
            "app_type",
            "users",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Configuration
        fields = [
            "id",
            "application",
            "name",
            "dev_settings",
            "uat_settings",
            "prod_settings",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "application", "created_at", "updated_at"]

    def _validate_settings_object(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Must be a JSON object.")
        return value

    def validate_dev_settings(self, value):
        return self._validate_settings_object(value)

    def validate_uat_settings(self, value):
        return self._validate_settings_object(value)

    def validate_prod_settings(self, value):
        return self._validate_settings_object(value)

    def validate(self, attrs):
        name = attrs.get("name", self.instance.name if self.instance else None)
        application_pk = self.context["view"].kwargs["application_pk"]
        conflict = Configuration.objects.filter(
            application_id=application_pk, name=name
        )
        if self.instance:
            conflict = conflict.exclude(pk=self.instance.pk)
        if conflict.exists():
            raise serializers.ValidationError(
                {"name": "Configuration with this name already exists for this application."}
            )
        return attrs
