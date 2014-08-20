from django.conf.urls import patterns, url
import views

urlpatterns = patterns('',
    url(r'^view/$', views.statuses, name='view'),
    url(r'^add/$', views.status_add, name='add'),
    url(r'^(?P<status_id>\d+)/edit/$', views.status_edit, name='edit'),
    url(r'^(?P<status_id>\d+)/delete/$', views.status_del, name='del'),
)