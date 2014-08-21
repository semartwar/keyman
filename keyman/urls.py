from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'keyman.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^organizations/', include('app_keyman.urls_organization', namespace='organizations')),
    url(r'^streets/', include('app_keyman.urls_street', namespace='streets')),
    url(r'^buildings/', include('app_keyman.urls_building', namespace='buildings')),
    url(r'^priorities/', include('app_keyman.urls_priority', namespace='priorities')),
    url(r'^statuses/', include('app_keyman.urls_order_status', namespace='statuses')),
    url(r'^orders/', include('app_keyman.urls', namespace='orders')),
    url(r'^users/', include('app_keyman.urls_users', namespace='users')),
    url(r'^logout/$', 'app_keyman.views.logout', name='logout'),
    url(r'^$', 'app_keyman.views.login', name='login'),
)