from django.shortcuts import get_object_or_404
from rest_framework import viewsets

from api.models import Application, Configuration, User
from api.serializers import ApplicationSerializer, ConfigurationSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer


class ConfigurationViewSet(viewsets.ModelViewSet):
    serializer_class = ConfigurationSerializer

    def get_queryset(self):
        get_object_or_404(Application, pk=self.kwargs["application_pk"])
        return Configuration.objects.filter(
            application_id=self.kwargs["application_pk"]
        )

    def perform_create(self, serializer):
        application = get_object_or_404(
            Application, pk=self.kwargs["application_pk"]
        )
        serializer.save(application=application)
