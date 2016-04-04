# Create your views here.
import inspect, json
from pprint import pprint as pp

from collections import OrderedDict

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from common.decorators import access_required
from common.helper_functions import instance_dict
from direct.pays.models import *
from direct.pays.forms import *

@access_required('direct.pays.admin')
def finance_codes(request):
    finance_codes = FinanceCode.objects.extra(select={'order': "cast(vcfinance_code as int)"}).all().extra(order_by=['order'])

    return render(request, 'pays/admin/finance_codes/index.html', {'finance_codes': finance_codes})

@access_required('direct.pays.admin')
def finance_codes_add(request):
    if request.method == 'POST':
        form = FinanceCodeForm(request.POST)

        if form.is_valid():
            fc = form.save()

            data = instance_dict(fc)
            data['method'] = 'add'

            dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
            return HttpResponse(json.dumps(data, default=dthandler), mimetype="application/json")

    else:
        form = FinanceCodeForm()

    return render(request, 'pays/admin/finance_codes/add.html', {'form': form})

@access_required('direct.pays.admin')
def finance_codes_edit(request, id):
    finance_code = FinanceCode.objects.get(pk=id)
    if request.method == 'POST':
        form = FinanceCodeForm(request.POST, instance=finance_code)
        if form.is_valid():
            fc = form.save()

            data = instance_dict(fc)
            data['method'] = 'edit'

            dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
            return HttpResponse(json.dumps(data, default=dthandler), mimetype="application/json")

    else:
        form = FinanceCodeForm(instance=finance_code)

    return render(request, 'pays/admin/finance_codes/edit.html', {'form': form})

@access_required('direct.pays.admin')
def cost_accounts(request):
    cost_accounts = CostAccount.objects.all()

    return render(request, 'pays/admin/cost_accounts/index.html', {'cost_accounts': cost_accounts})

@access_required('direct.pays.admin')
def cost_accounts_add(request):
    if request.method == 'POST':
        form = CostAccountForm(request.POST)
        if form.is_valid():
            ca = form.save()

            data = instance_dict(ca)
            data['location'] = ca.location.location
            data['method'] = 'add'

            dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
            return HttpResponse(json.dumps(data, default=dthandler), mimetype="application/json")

    else:
        form = CostAccountForm()

    return render(request, 'pays/admin/cost_accounts/add.html', {'form': form})

@access_required('direct.pays.admin')
def cost_accounts_edit(request, id):
    cost_account = CostAccount.objects.get(pk=id)
    if request.method == 'POST':
        form = CostAccountForm(request.POST, instance=cost_account)
        if form.is_valid():
            ca = form.save()

            data = instance_dict(ca)
            data['location'] = ca.location.location
            data['method'] = 'edit'

            dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
            return HttpResponse(json.dumps(data, default=dthandler), mimetype="application/json")

    else:
        form = CostAccountForm(instance=cost_account)

    return render(request, 'pays/admin/cost_accounts/edit.html', {'form': form})
