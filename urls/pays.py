from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('direct.pays',
    url(r'^$', 'views.pays.index'),

    url(r'^calculate/(?P<cycle_id>\d+)/$', 'views.pays.calculate'),
    url(r'^calculating/(?P<cycle_id>\d+)/(?P<pay_run_id>\d+)/$', 'views.pays.calculating'),

    url(r'^lock/(?P<cycle_id>\d+)/$', 'views.pays.lock'),
    url(r'^unlock/(?P<cycle_id>\d+)/$', 'views.pays.unlock'),

    url(r'^add/$', 'views.pays.add'),
    url(r'^upload/$', 'views.pays.upload'),
    url(r'^search/$', 'views.pays.search'),

    url(r'^held/$', 'views.pays.held'),
    url(r'^perm_held/$', 'views.pays.perm_held'),
)
