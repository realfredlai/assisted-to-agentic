from django.db import models


class User(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Application(models.Model):
    class AppType(models.TextChoices):
        MOBILE = "mobile"
        DESKTOP = "desktop"
        WEB = "web"
        CLOUD = "cloud"

    name = models.CharField(max_length=100, unique=True)
    app_type = models.CharField(max_length=10, choices=AppType.choices)
    users = models.ManyToManyField(User, related_name="applications", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Configuration(models.Model):
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="configurations"
    )
    name = models.CharField(max_length=100)
    dev_settings = models.JSONField(default=dict, blank=True)
    uat_settings = models.JSONField(default=dict, blank=True)
    prod_settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["application", "name"],
                name="unique_configuration_name_per_application",
            )
        ]

    def __str__(self):
        return f"{self.application.name}/{self.name}"
