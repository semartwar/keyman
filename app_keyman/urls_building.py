from django.conf.urls import patterns, url
import views

urlpatterns = patterns('',
    url(r'^view/$', views.buildings, name='view'),
    url(r'^add/$', views.building_add, name='add'),
    url(r'^(?P<building_id>\d+)/delete/$', views.building_del, name='del'),
)