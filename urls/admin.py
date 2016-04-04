from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('direct.pays.views.admin',
    url(r'^finance_codes/$', 'finance_codes'),
    url(r'^finance_codes/add/$', 'finance_codes_add'),
    url(r'^finance_codes/(?P<id>\d+)/$', 'finance_codes_edit'),

    url(r'^cost_accounts/$', 'cost_accounts'),
    url(r'^cost_accounts/add/$', 'cost_accounts_add'),
    url(r'^cost_accounts/(?P<id>\d+)/$', 'cost_accounts_edit'),
)
