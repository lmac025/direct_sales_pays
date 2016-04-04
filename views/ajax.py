# Create your views here.
import inspect
import json
from pprint import pprint as pp

from annoying.decorators import ajax_request
from collections import OrderedDict

from django.core.urlresolvers import reverse
from django.db.models import Q, Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from common.helper_functions import to_select
from common.decorators import access_required
from direct.pays.models import *
from direct.pays.forms import *

def remove_payline(request, payline_id):
    payline = Payline.objects.get(pk=payline_id)
    if payline.manual:
        payline.active = False
    else:
        payline.perm_held = True

    payline.save()

    return HttpResponse('')

def hold_payline(request, payline_id):
    payline = Payline.objects.get(pk=payline_id)
    payline.held = True
    payline.save()

    return HttpResponse('')

def unhold_payline(request, payline_id):
    payline = Payline.objects.get(pk=payline_id)
    payline.held = False
    payline.save()

    return HttpResponse('')

def perm_hold_payline(request, payline_id):
    payline = Payline.objects.get(pk=payline_id)
    payline.perm_held = True
    payline.save()

    return HttpResponse('')

def retrieve_payline(request, payline_id):
    payline = Payline.objects.get(pk=payline_id)
    payline.perm_held = False
    payline.held = True
    payline.save()

    return HttpResponse('')

def release_payline(request, payline_id, release_cycle_id):
    payline = Payline.objects.get(pk=payline_id)
    release_cycle = Cycle.objects.get(pk=release_cycle_id)
    pay_run = PayRun()
    pay_run.id = 0
    release_payline = payline
    release_payline.id = None

    release_payline.held = False
    release_payline.last_altered_by = request.user.get('username')
    release_payline.cycle = release_cycle
    release_payline.pay_run = pay_run
    release_payline.calculated = False
    release_payline.manual = False
    release_payline.reference_payline = None
    release_payline.save()

    payline = Payline.objects.get(pk=payline_id)
    payline.reference_payline = release_payline
    payline.save()

    return HttpResponse('')

def hold_finance_code(request, finance_code_id, contractor_id, cycle_id, pay_run_id):
    paylines = Payline.objects.all().filter(Q(pay_run=pay_run_id) | Q(pay_run=0),
                                                            cycle=cycle_id,
                                                            finance_code=finance_code_id,
                                                            contractor=contractor_id,
                                                            active=True,
                                                            dummy=False,
                                                            held=False)
    for payline in paylines:
        payline.held = True
        payline.save()

    return HttpResponse('')

def unhold_finance_code(request, finance_code_id, contractor_id, cycle_id, pay_run_id):
    paylines = Payline.objects.all().filter(Q(pay_run=pay_run_id) | Q(pay_run=0),
                                                            cycle=cycle_id,
                                                            finance_code=finance_code_id,
                                                            contractor=contractor_id,
                                                            active=True,
                                                            dummy=False,
                                                            held=True)
    for payline in paylines:
        payline.held = False
        payline.save()

    return HttpResponse('')

def perm_hold_finance_code(request, finance_code_id, cycle_id, contractor_id):
    held_paylines = Payline.objects.all().filter(Q(pay_run__approved=True) | Q(pay_run=0),
                                                    cycle=cycle_id,
                                                    finance_code=finance_code_id,
                                                    contractor=contractor_id,
                                                    active=True,
                                                    dummy=False,
                                                    perm_held=False,
                                                    held=True,
                                                    reference_payline=None)
    for payline in held_paylines:
        payline.perm_held = True
        payline.save()

    return HttpResponse('')

def retrieve_finance_code(request, finance_code_id, cycle_id, contractor_id):
    held_paylines = Payline.objects.all().filter(Q(pay_run__approved=True) | Q(pay_run=0),
                                                    cycle=cycle_id,
                                                    finance_code=finance_code_id,
                                                    contractor=contractor_id,
                                                    active=True,
                                                    dummy=False,
                                                    perm_held=True)

    for payline in held_paylines:
        payline.perm_held = False
        payline.held = True
        payline.save()

    return HttpResponse('')

def release_finance_code(request, finance_code_id, cycle_id, contractor_id, release_cycle_id):
    held_paylines = Payline.objects.all().filter(Q(pay_run__approved=True) | Q(pay_run=0),
                                                    cycle=cycle_id,
                                                    finance_code=finance_code_id,
                                                    contractor=contractor_id,
                                                    active=True,
                                                    dummy=False,
                                                    perm_held=False,
                                                    held=True,
                                                    reference_payline=None)
    for payline in held_paylines:
        payline_id = payline.id

        release_cycle = Cycle.objects.get(pk=release_cycle_id)
        pay_run = PayRun()
        pay_run.id = 0
        release_payline = payline
        release_payline.id = None

        release_payline.held = False
        release_payline.last_altered_by = request.user.get('username')
        release_payline.cycle = release_cycle
        release_payline.pay_run = pay_run
        release_payline.calculated = False
        release_payline.manual = False
        release_payline.reference_payline = None
        release_payline.save()

        orig_payline = Payline.objects.get(pk=payline_id)
        orig_payline.reference_payline = release_payline
        orig_payline.save()

    return HttpResponse('')

def hold_contractor(request, contractor_id, cycle_id, pay_run_id):
    paylines = Payline.objects.all().filter(Q(pay_run=pay_run_id) | Q(pay_run=0),
                                                            cycle=cycle_id,
                                                            contractor=contractor_id,
                                                            active=True,
                                                            dummy=False,
                                                            held=False)
    for payline in paylines:
        payline.held = True
        payline.save()

    return HttpResponse('')

def unhold_contractor(request, contractor_id, cycle_id, pay_run_id):
    paylines = Payline.objects.all().filter(Q(pay_run=pay_run_id) | Q(pay_run=0),
                                                            cycle=cycle_id,
                                                            contractor=contractor_id,
                                                            active=True,
                                                            dummy=False,
                                                            held=True)
    for payline in paylines:
        payline.held = False
        payline.save()

    return HttpResponse('')

def perm_hold_contractor(request, contractor_id):
    held_paylines = Payline.objects.all().filter(Q(pay_run__approved=True) | Q(pay_run=0),
                                                    cycle__locked=True,
                                                    contractor=contractor_id,
                                                    active=True,
                                                    dummy=False,
                                                    perm_held=False,
                                                    held=True,
                                                    reference_payline=None)

    for payline in held_paylines:
        payline.perm_held = True
        payline.save()

    return HttpResponse('')

def retrieve_contractor(request, contractor_id):
    held_paylines = Payline.objects.all().filter(Q(pay_run__approved=True) | Q(pay_run=0),
                                                    contractor=contractor_id,
                                                    active=True,
                                                    dummy=False,
                                                    perm_held=True)

    for payline in held_paylines:
        payline.perm_held = False
        payline.held = True
        payline.save()

    return HttpResponse('')

def release_contractor(request, contractor_id, release_cycle_id):
    held_paylines = Payline.objects.all().filter(Q(pay_run__approved=True) | Q(pay_run=0),
                                                    cycle__locked=True,
                                                    contractor=contractor_id,
                                                    active=True,
                                                    dummy=False,
                                                    perm_held=False,
                                                    held=True,
                                                    reference_payline=None)
    for payline in held_paylines:
        payline_id = payline.id

        release_cycle = Cycle.objects.get(pk=release_cycle_id)
        pay_run = PayRun()
        pay_run.id = 0
        release_payline = payline
        release_payline.id = None

        release_payline.held = False
        release_payline.last_altered_by = request.user.get('username')
        release_payline.cycle = release_cycle
        release_payline.pay_run = pay_run
        release_payline.calculated = False
        release_payline.manual = False
        release_payline.reference_payline = None
        release_payline.save()

        orig_payline = Payline.objects.get(pk=payline_id)
        orig_payline.reference_payline = release_payline
        orig_payline.save()

    return HttpResponse('')

def perm_hold_cycle(request, cycle_id, contractor_id):
    held_paylines = Payline.objects.all().filter(Q(pay_run__approved=True) | Q(pay_run=0),
                                                    cycle=cycle_id,
                                                    contractor=contractor_id,
                                                    active=True,
                                                    dummy=False,
                                                    perm_held=False,
                                                    held=True,
                                                    reference_payline=None)

    for payline in held_paylines:
        payline.perm_held = True
        payline.save()

    return HttpResponse('')

def retrieve_cycle(request, cycle_id, contractor_id):
    held_paylines = Payline.objects.all().filter(Q(pay_run__approved=True) | Q(pay_run=0),
                                                    cycle=cycle_id,
                                                    contractor=contractor_id,
                                                    active=True,
                                                    dummy=False,
                                                    perm_held=True)

    for payline in held_paylines:
        payline.perm_held = False
        payline.held = True
        payline.save()

    return HttpResponse('')

def release_cycle(request, cycle_id, contractor_id, release_cycle_id):
    held_paylines = Payline.objects.all().filter(Q(pay_run__approved=True) | Q(pay_run=0),
                                                    cycle=cycle_id,
                                                    contractor=contractor_id,
                                                    active=True,
                                                    dummy=False,
                                                    perm_held=False,
                                                    held=True,
                                                    reference_payline=None)
    for payline in held_paylines:
        payline_id = payline.id

        release_cycle = Cycle.objects.get(pk=release_cycle_id)
        pay_run = PayRun()
        pay_run.id = 0
        release_payline = payline
        release_payline.id = None

        release_payline.held = False
        release_payline.last_altered_by = request.user.get('username')
        release_payline.cycle = release_cycle
        release_payline.pay_run = pay_run
        release_payline.calculated = False
        release_payline.manual = False
        release_payline.reference_payline = None
        release_payline.save()

        orig_payline = Payline.objects.get(pk=payline_id)
        orig_payline.reference_payline = release_payline
        orig_payline.save()

    return HttpResponse('')

@never_cache
def check_pay_run(request, pay_run_id):
    pay_run = PayRun.objects.get(pk=pay_run_id)
    calculation_progress = CalculationProgress.objects.all().filter(pay_run=pay_run, cycle=pay_run.cycle)
    
    data = {}
    for c in calculation_progress:
        data.setdefault('steps', {}).setdefault(c.step, []).append(c.sub_step)
    data['calculated'] = pay_run.calculated
    data['failed'] = pay_run.failed

    return HttpResponse(json.dumps(data), mimetype="application/json")

@never_cache
def fetch_paylines(request, cycle_id, pay_run_id):
    id = request.GET.get('id')
    type = request.GET.get('type')
    location = request.GET.get('l')

    config = Config.objects.get(application='pays')

    current_cycle = Cycle.objects.get(pk=cycle_id)

    paylines_dict = OrderedDict()
    held_paylines_dict = OrderedDict()
    totals = {}
    
    if type == 'contractors':
        paylines = Payline.objects.values_list('contractor__id').distinct().filter(Q(pay_run=pay_run_id) | Q(pay_run=0), cycle=cycle_id, active=True, dummy=False, perm_held=False).order_by('-contractor__payroll')
        if location:
            paylines = paylines.filter(location=location)
        contractors = [p[0] for p in paylines]

        return HttpResponse(json.dumps(contractors), mimetype="application/json")

    if type == 'paylines':
        paylines = Payline.objects.select_related().all().filter(Q(pay_run=pay_run_id) | Q(pay_run=0), contractor=id, cycle=cycle_id, active=True, dummy=False, held=False, perm_held=False)
        if location:
            paylines = paylines.filter(location=location)

        for payline in paylines:
            contractor_id = payline.contractor.id
            finance_code_id = payline.finance_code.id
            if not contractor_id in paylines_dict:
                paylines_dict[contractor_id] = {}
                paylines_dict[contractor_id]['contractor'] = payline.contractor
                paylines_dict[contractor_id]['total'] = 0
                paylines_dict[contractor_id]['total_gst'] = 0
                paylines_dict[contractor_id]['manual'] = False
                paylines_dict[contractor_id]['finance_codes'] = OrderedDict()
            if not finance_code_id in paylines_dict[contractor_id]['finance_codes']:
                paylines_dict[contractor_id]['finance_codes'][finance_code_id] = {}
                paylines_dict[contractor_id]['finance_codes'][finance_code_id]['finance_code'] = payline.finance_code
                paylines_dict[contractor_id]['finance_codes'][finance_code_id]['total'] = 0
                paylines_dict[contractor_id]['finance_codes'][finance_code_id]['total_gst'] = 0
                paylines_dict[contractor_id]['finance_codes'][finance_code_id]['manual'] = False
                paylines_dict[contractor_id]['finance_codes'][finance_code_id]['paylines'] = []

            if payline.manual:
                paylines_dict[contractor_id]['manual'] = True
                paylines_dict[contractor_id]['finance_codes'][finance_code_id]['manual'] = True

            paylines_dict[contractor_id]['total'] += payline.value
            paylines_dict[contractor_id]['total_gst'] += float(payline.gst_value or 0)

            paylines_dict[contractor_id]['finance_codes'][finance_code_id]['total'] += payline.value
            paylines_dict[contractor_id]['finance_codes'][finance_code_id]['total_gst'] += float(payline.gst_value or 0)

            paylines_dict[contractor_id]['finance_codes'][finance_code_id]['paylines'].append(payline)

    if type == 'held_paylines':
        held_paylines = Payline.objects.select_related().all().filter(Q(pay_run=pay_run_id) | Q(pay_run=0), contractor=id, cycle=cycle_id, active=True, dummy=False, perm_held=False, held=True)
        if location:
            held_paylines = held_paylines.filter(location=location)


        for payline in held_paylines:
            contractor_id = payline.contractor.id
            finance_code_id = payline.finance_code.id
            if not contractor_id in held_paylines_dict:
                held_paylines_dict[contractor_id] = {}
                held_paylines_dict[contractor_id]['contractor'] = payline.contractor
                held_paylines_dict[contractor_id]['total'] = 0.0
                held_paylines_dict[contractor_id]['total_gst'] = 0.0
                held_paylines_dict[contractor_id]['finance_codes'] = OrderedDict()
            if not finance_code_id in held_paylines_dict[contractor_id]['finance_codes']:
                held_paylines_dict[contractor_id]['finance_codes'][finance_code_id] = {}
                held_paylines_dict[contractor_id]['finance_codes'][finance_code_id]['finance_code'] = payline.finance_code
                held_paylines_dict[contractor_id]['finance_codes'][finance_code_id]['total'] = 0.0
                held_paylines_dict[contractor_id]['finance_codes'][finance_code_id]['total_gst'] = 0.0
                held_paylines_dict[contractor_id]['finance_codes'][finance_code_id]['paylines'] = []

            held_paylines_dict[contractor_id]['total'] += payline.value
            held_paylines_dict[contractor_id]['total_gst'] += float(payline.gst_value or 0)

            held_paylines_dict[contractor_id]['finance_codes'][finance_code_id]['total'] += payline.value
            held_paylines_dict[contractor_id]['finance_codes'][finance_code_id]['total_gst'] += float(payline.gst_value or 0)

            held_paylines_dict[contractor_id]['finance_codes'][finance_code_id]['paylines'].append(payline)

    if type == 'totals':
        totals = Payline.objects.values('finance_code__description').filter(Q(pay_run=pay_run_id) | Q(pay_run=0), cycle=cycle_id, active=True, dummy=False, held=False, perm_held=False).annotate(value_sum=Sum('value')).order_by('finance_code__description')
        if location:
            totals = totals.filter(location=location)
        
    return render(request, 'pays/ajax/paylines.html', {'pay_run_id': pay_run_id,
                                                        'cycle_id': cycle_id,
                                                        'paylines': paylines_dict,
                                                        'held_paylines': held_paylines_dict,
                                                        'totals': totals,
                                                        'current_cycle': current_cycle,
                                                        'config': config})

@never_cache
def fetch_contractors(request):
    contractors = [c.get('id') for c in Contractor.objects.values('id').order_by('-payroll')]

    return HttpResponse(json.dumps(contractors), mimetype="application/json")

@never_cache
def fetch_held_paylines(request):
    id = request.GET.get('id')

    if request.GET.get('contractors'):
        held_paylines = Payline.objects.values_list('contractor__id').distinct().all().filter(Q(pay_run__approved=True) | Q(pay_run=0), cycle__locked=True, active=True, dummy=False, perm_held=False, held=True, reference_payline=None).order_by('-contractor__payroll')

        contractors = [p[0] for p in held_paylines]

        return HttpResponse(json.dumps(contractors), mimetype="application/json")

    unlocked_cycles = Cycle.objects.values('id', 'cycle_date').order_by('-id').filter(locked=False, active=True)
    form = CalculationForm(request.GET)
    form.fields['c'].widget.choices = to_select(unlocked_cycles, 'id', 'cycle_date', '----------------', 'date')
    form.fields['c'].widget.attrs = {'class':'release'}

    held_paylines = Payline.objects.select_related().all().filter(Q(pay_run__approved=True) | Q(pay_run=0), contractor=id, cycle__locked=True, active=True, dummy=False, perm_held=False, held=True, reference_payline=None)

    held_paylines_dict = OrderedDict()

    for payline in held_paylines:
        contractor_id = payline.contractor.id
        finance_code_id = payline.finance_code.id
        cycle_id = payline.cycle.id
        if not contractor_id in held_paylines_dict:
            held_paylines_dict[contractor_id] = {}
            held_paylines_dict[contractor_id]['contractor'] = payline.contractor
            held_paylines_dict[contractor_id]['total'] = 0.0
            held_paylines_dict[contractor_id]['total_gst'] = 0.0
            held_paylines_dict[contractor_id]['cycles'] = OrderedDict()
        if not cycle_id in held_paylines_dict[contractor_id]['cycles']:
            held_paylines_dict[contractor_id]['cycles'][cycle_id] = {}
            held_paylines_dict[contractor_id]['cycles'][cycle_id]['cycle'] = payline.cycle
            held_paylines_dict[contractor_id]['cycles'][cycle_id]['total'] = 0.0
            held_paylines_dict[contractor_id]['cycles'][cycle_id]['total_gst'] = 0.0
            held_paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'] = OrderedDict()
        if not finance_code_id in held_paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes']:
            held_paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'][finance_code_id] = {}
            held_paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'][finance_code_id]['finance_code'] = payline.finance_code
            held_paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'][finance_code_id]['total'] = 0.0
            held_paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'][finance_code_id]['total_gst'] = 0.0
            held_paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'][finance_code_id]['paylines'] = []

        held_paylines_dict[contractor_id]['total'] += payline.value
        held_paylines_dict[contractor_id]['total_gst'] += float(payline.gst_value or 0)

        held_paylines_dict[contractor_id]['cycles'][cycle_id]['total'] += payline.value
        held_paylines_dict[contractor_id]['cycles'][cycle_id]['total_gst'] += float(payline.gst_value or 0)

        held_paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'][finance_code_id]['total'] += payline.value
        held_paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'][finance_code_id]['total_gst'] += float(payline.gst_value or 0)

        held_paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'][finance_code_id]['paylines'].append(payline)

    return render(request, 'pays/ajax/held_paylines.html',   {'held_paylines': held_paylines_dict,
                                                                'form': form})

@never_cache
def fetch_permheld_paylines(request):
    id = request.GET.get('id')

    if request.GET.get('contractors'):
        held_paylines = Payline.objects.values_list('contractor__id').distinct().all().filter(Q(pay_run__approved=True) | Q(pay_run=0), active=True, dummy=False, perm_held=True, reference_payline=None).order_by('-contractor__payroll')

        contractors = [p[0] for p in held_paylines]

        return HttpResponse(json.dumps(contractors), mimetype="application/json")

    held_paylines = Payline.objects.select_related().all().filter(Q(pay_run__approved=True) | Q(pay_run=0), contractor=id, active=True, dummy=False, perm_held=True, reference_payline=None)

    held_paylines_dict = OrderedDict()

    for payline in held_paylines:
        contractor_id = payline.contractor.id
        finance_code_id = payline.finance_code.id
        cycle_id = payline.cycle.id
        if not contractor_id in held_paylines_dict:
            held_paylines_dict[contractor_id] = {}
            held_paylines_dict[contractor_id]['contractor'] = payline.contractor
            held_paylines_dict[contractor_id]['total'] = 0.0
            held_paylines_dict[contractor_id]['total_gst'] = 0.0
            held_paylines_dict[contractor_id]['cycles'] = OrderedDict()
        if not cycle_id in held_paylines_dict[contractor_id]['cycles']:
            held_paylines_dict[contractor_id]['cycles'][cycle_id] = {}
            held_paylines_dict[contractor_id]['cycles'][cycle_id]['cycle'] = payline.cycle
            held_paylines_dict[contractor_id]['cycles'][cycle_id]['total'] = 0.0
            held_paylines_dict[contractor_id]['cycles'][cycle_id]['total_gst'] = 0.0
            held_paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'] = OrderedDict()
        if not finance_code_id in held_paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes']:
            held_paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'][finance_code_id] = {}
            held_paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'][finance_code_id]['finance_code'] = payline.finance_code
            held_paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'][finance_code_id]['total'] = 0.0
            held_paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'][finance_code_id]['total_gst'] = 0.0
            held_paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'][finance_code_id]['paylines'] = []

        held_paylines_dict[contractor_id]['total'] += payline.value
        held_paylines_dict[contractor_id]['total_gst'] += float(payline.gst_value or 0)

        held_paylines_dict[contractor_id]['cycles'][cycle_id]['total'] += payline.value
        held_paylines_dict[contractor_id]['cycles'][cycle_id]['total_gst'] += float(payline.gst_value or 0)

        held_paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'][finance_code_id]['total'] += payline.value
        held_paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'][finance_code_id]['total_gst'] += float(payline.gst_value or 0)

        held_paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'][finance_code_id]['paylines'].append(payline)

    return render(request, 'pays/ajax/perm_held_paylines.html',   {'held_paylines': held_paylines_dict})
