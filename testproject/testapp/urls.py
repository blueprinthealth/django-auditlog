from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns(
    '',
    url(r'^$', views.test_view, name='test'),
    url(r'^apitest/$', views.TestAPIView.as_view(), name='apitest'),
)
