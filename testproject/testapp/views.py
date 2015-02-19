from testapp import models
from django.http import HttpResponse
from rest_framework import generics, serializers
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from auditlog.view_audit import DRFViewMixin


def test_view(request):
    for test_model in models.TestModelOne.objects.all():
        test_model.save()

    for test_model in models.TestModelTwo.objects.all():
        test_model.save()

    return HttpResponse()


class TestModelOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TestModelOne


class TestAPIView(DRFViewMixin, generics.CreateAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = models.TestModelOne.objects.all()
    serializer_class = TestModelOneSerializer
