from django.conf.urls import patterns, url
import views

urlpatterns = patterns('',
    url(r'^view/$', views.priorities, name='view'),
    url(r'^add/$', views.priority_add, name='add'),
    url(r'^(?P<priority_id>\d+)/edit/$', views.priority_edit, name='edit'),
    url(r'^(?P<priority_id>\d+)/delete/$', views.priority_del, name='del'),
)