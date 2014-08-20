from django.conf.urls import patterns, url
import views

urlpatterns = patterns('',
    url(r'^view/$', views.users, name='view'),
    url(r'^add/$', views.user_add, name='add'),
    url(r'^(?P<user_id>\d+)/delete/$', views.user_del, name='del'),
)