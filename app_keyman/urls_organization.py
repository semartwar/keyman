from django.conf.urls import patterns, url
import views

urlpatterns = patterns('',
    url(r'^view/$', views.organizations, name='view'),
    url(r'^add/$', views.organization_add, name='add'),
    url(r'^(?P<organization_id>\d+)/delete/$', views.organization_del, name='del'),
)