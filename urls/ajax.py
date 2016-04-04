from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('direct.pays.views.ajax',
    url(r'^check_pay_run/(?P<pay_run_id>\d+)/$', 'check_pay_run'),

    url(r'^fetch/paylines/(?P<cycle_id>\d+)/(?P<pay_run_id>\d+)/$', 'fetch_paylines'),
    url(r'^fetch/held/$', 'fetch_held_paylines'),
    url(r'^fetch/contractors/$', 'fetch_contractors'),
    url(r'^fetch/perm_held/$', 'fetch_permheld_paylines'),

    url(r'^remove/payline/(?P<payline_id>\d+)/$', 'remove_payline'),

    url(r'^hold/payline/(?P<payline_id>\d+)/$', 'hold_payline'),
    url(r'^hold/finance_code/(?P<finance_code_id>\d+)/(?P<contractor_id>\d+)/(?P<cycle_id>\d+)/(?P<pay_run_id>\d+)/$', 'hold_finance_code'),
    url(r'^hold/contractor/(?P<contractor_id>\d+)/(?P<cycle_id>\d+)/(?P<pay_run_id>\d+)/$', 'hold_contractor'),

    url(r'^perm_hold/payline/(?P<payline_id>\d+)/$', 'perm_hold_payline'),
    url(r'^perm_hold/finance_code/(?P<finance_code_id>\d+)/(?P<cycle_id>\d+)/(?P<contractor_id>\d+)/$', 'perm_hold_finance_code'),
    url(r'^perm_hold/cycle/(?P<cycle_id>\d+)/(?P<contractor_id>\d+)/$', 'perm_hold_cycle'),
    url(r'^perm_hold/contractor/(?P<contractor_id>\d+)/$', 'perm_hold_contractor'),

    url(r'^unhold/payline/(?P<payline_id>\d+)/$', 'unhold_payline'),
    url(r'^unhold/finance_code/(?P<finance_code_id>\d+)/(?P<contractor_id>\d+)/(?P<cycle_id>\d+)/(?P<pay_run_id>\d+)/$', 'unhold_finance_code'),
    url(r'^unhold/contractor/(?P<contractor_id>\d+)/(?P<cycle_id>\d+)/(?P<pay_run_id>\d+)/$', 'unhold_contractor'),

    url(r'^retrieve/payline/(?P<payline_id>\d+)/$', 'retrieve_payline'),
    url(r'^retrieve/finance_code/(?P<finance_code_id>\d+)/(?P<cycle_id>\d+)/(?P<contractor_id>\d+)/$', 'retrieve_finance_code'),
    url(r'^retrieve/cycle/(?P<cycle_id>\d+)/(?P<contractor_id>\d+)/$', 'retrieve_cycle'),
    url(r'^retrieve/contractor/(?P<contractor_id>\d+)/$', 'retrieve_contractor'),

    url(r'^release/payline/(?P<payline_id>\d+)/(?P<release_cycle_id>\d+)/$', 'release_payline'),
    url(r'^release/finance_code/(?P<finance_code_id>\d+)/(?P<cycle_id>\d+)/(?P<contractor_id>\d+)/(?P<release_cycle_id>\d+)/$', 'release_finance_code'),
    url(r'^release/cycle/(?P<cycle_id>\d+)/(?P<contractor_id>\d+)/(?P<release_cycle_id>\d+)/$', 'release_cycle'),
    url(r'^release/contractor/(?P<contractor_id>\d+)/(?P<release_cycle_id>\d+)/$', 'release_contractor'),
)
