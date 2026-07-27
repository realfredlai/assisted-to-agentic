from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import ApplicationViewSet, ConfigurationViewSet, UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"applications", ApplicationViewSet)

configuration_list = ConfigurationViewSet.as_view({"get": "list", "post": "create"})
configuration_detail = ConfigurationViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "applications/<int:application_pk>/configurations/",
        configuration_list,
        name="application-configurations-list",
    ),
    path(
        "applications/<int:application_pk>/configurations/<int:pk>/",
        configuration_detail,
        name="application-configurations-detail",
    ),
]
