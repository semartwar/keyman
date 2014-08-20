from django.conf.urls import patterns, url
import views

urlpatterns = patterns('',
    url(r'^view/$', views.orders, name='view'),
    url(r'^add/$', views.order_add, name='add'),
    url(r'^(?P<order_id>\d+)/edit/$', views.order_edit, name='edit'),
    url(r'^(?P<order_id>\d+)/cancel/$', views.order_cancel, name='cancel'),
)