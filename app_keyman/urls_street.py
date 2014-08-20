from django.conf.urls import patterns, url
import views

urlpatterns = patterns('',
    url(r'^view/$', views.streets, name='view'),
    url(r'^add/$', views.street_add, name='add'),
    url(r'^(?P<street_id>\d+)/delete/$', views.street_del, name='del'),
)