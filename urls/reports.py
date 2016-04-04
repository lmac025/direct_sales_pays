from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('direct.pays.views.reports',
    url(r'^held/$', 'held'),
    url(r'^paylines/(?P<cycle_id>\d+)/$', 'paylines'),
    url(r'^payline_summary/(?P<cycle_id>\d+)/$', 'payline_summary'),
    url(r'^payroll_files/(?P<cycle_id>\d+)/$', 'payroll_files'),

    url(r'^commission_statements/(?P<cycle_id>\d+)/$', 'commission_statements'),
    url(r'^tax_invoices/(?P<cycle_id>\d+)/$', 'tax_invoices'),
)
