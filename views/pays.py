## Create your views here.
import inspect, datetime, redis, string
from pprint import pprint as pp

from common.servers import get_redis
from collections import OrderedDict

from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.db import connections, transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from common.helper_functions import to_select, map_to_key, send_email
from common.decorators import access_required
from direct.pays.models import *
from direct.pays.forms import *

from StringIO import StringIO

@access_required('direct.pays.access')
def home(request):
    project_access = request.user['permissions'].get('direct.pays.access', [])
    return render(request, 'pays/home.html', {'project_access': project_access})
    
@access_required('direct.pays.access')
def index(request):
    config = Config.objects.get(application='pays')
    failed = request.GET.get('failed', 'False')
    location = request.GET.get('l', '')
    if failed == 'True':
        messages.error(request, 'The last calculation failed. Please notify helpdesk to fix the calculation process.')

    cycles = Cycle.objects.values().order_by('-id').filter(active=True)
    locations = Location.objects.values().order_by('location')

    if not request.info.get('current_projectname') in request.user['perms'].get('direct.pays.admin', {}):
        cycles = cycles.filter(locked=True)

    form = CalculationForm(request.GET)
    form.fields['c'].widget.choices = to_select(cycles, 'id', 'cycle_date', None, 'date')
    form.fields['l'].widget.choices = to_select(locations, 'id', 'location')

    cycles = Cycle.objects.all().order_by('-id')
    if not request.info.get('current_projectname') in request.user['perms'].get('direct.pays.admin', {}):
        cycles = cycles.filter(locked=True)

    cycle_id = int(request.GET.get('c', cycles[0].id))
    current_cycle = Cycle.objects.get(pk=cycle_id)

    pay_runs = PayRun.objects.all().filter(cycle=cycle_id).order_by('-approved')
    try:
        pay_run_id = int(request.GET.get('pr', pay_runs[0].id))
    except:
        pay_run_id = 0

    try:
        pay_run = PayRun.objects.get(cycle=cycle_id, approved=True)
        if not pay_run.calculated:
            return HttpResponseRedirect(reverse('direct.pays.views.pays.calculating', args=[request.info.get('current_projectname'), cycle_id, pay_run.id]))
    except:
        pass

    pay_runs = pay_runs.order_by('id')

    if not pay_runs:
        pay_run = PayRun()
        pay_run.created_by = 'Noone'
        pay_run.created_date = datetime.datetime.now()
        pay_run.id = 0

        pay_runs = [pay_run]

    return render(request, 'pays/pays/index.html', {'current_cycle': current_cycle,
                                                    'pay_runs': pay_runs,
                                                    'pay_run_id': pay_run_id,
                                                    'form': form,
                                                    'config': config,
                                                    'location': location})
@access_required('direct.pays.access')
def search(request):
    config = Config.objects.get(application='pays')

    paylines = {}
    messages.info(request, 'To prevent timeouts search only returns the first 500 matching paylines.')

    form = SearchForm(request.GET)
    cycles = Cycle.objects.values().order_by('-id')
    locations = Location.objects.values('id', 'location')
    finance_codes = FinanceCode.objects.extra(select={'display': "vcfinance_code+' - '+vcdescription", 'order': "cast(vcfinance_code as int)"}).values('id','display', 'order').extra(order_by=['order'])

    form.fields['cycle'].widget.choices = to_select(cycles, 'id', 'cycle_date', '------------', 'date')
    form.fields['finance_code'].widget.choices = to_select(finance_codes, 'id', 'display')
    form.fields['location'].widget.choices = to_select(locations, 'id', 'location')

    
    query_string = request.META['QUERY_STRING']
    if any([bool(request.GET.get(x)) for x in request.GET]) and all(k not in form.errors for k in ('pay_id', 'payroll')):
        paylines = Payline.objects.select_related().all().filter(Q(pay_run__approved=True) | Q(pay_run=0), active=True, dummy=False)

        if request.GET.get('cycle'):
            paylines = paylines.filter(cycle=request.GET.get('cycle'))

        if request.GET.get('location'):
            paylines = paylines.filter(location=request.GET.get('location'))

        if request.GET.get('finance_code'):
            paylines = paylines.filter(finance_code=request.GET.get('finance_code'))

        if request.GET.get('sales_code'):
            paylines = paylines.filter(contractor__sales_code__contains=request.GET.get('sales_code'))

        if request.GET.get('payroll'):
            paylines = paylines.filter(contractor__payroll__contains=request.GET.get('payroll'))

        if request.GET.get('application_id'):
            paylines = paylines.filter(application_id__contains=request.GET.get('application_id'))

        if request.GET.get('pay_id'):
            paylines = paylines.filter(external_record_id=request.GET.get('pay_id'))

        paylines = paylines[:500]

        if not paylines:
            messages.warning(request, 'No paylines were found matching your criteria')


    if request.GET.get('fmt') == 'excel':
        head_row = (
            "Finance Code", "Location", "Contractor Id", "Sales Code", "Contractor", "Payroll",
            "Amount", "GST", "Details", "Pays Id", "Application Id", "Cycle"
        )

        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=Search Extract.csv'

        xstr = lambda s: s or ""


        writer = csv.writer(response, quoting=csv.QUOTE_ALL)
        writer.writerow(head_row)
        for payline in paylines:
            row = [payline.finance_code.description, payline.location, payline.contractor.id, payline.contractor.sales_code,
                    payline.contractor.name, payline.contractor.payroll, payline.value, payline.gst_value,
                    xstr(payline.details).encode('utf8'),
                    payline.external_record_id, payline.application_id, payline.cycle.cycle_date]
            if payline.perm_held:
                row.append("Perm Held")
            elif not payline.reference_payline == None:
                row.append("Held and Released")
            elif payline.held:
                row.append("Held")

            writer.writerow(row)

        return response

    else:
        paylines_dict = OrderedDict()

        for payline in paylines:
            contractor_id = payline.contractor.id
            cycle_id = payline.cycle.id
            finance_code_id = payline.finance_code.id
            if not contractor_id in paylines_dict:
                paylines_dict[contractor_id] = {}
                paylines_dict[contractor_id]['contractor'] = payline.contractor
                paylines_dict[contractor_id]['cycles'] = OrderedDict()

            if not cycle_id in paylines_dict[contractor_id]['cycles']:
                paylines_dict[contractor_id]['cycles'][cycle_id] = {}
                paylines_dict[contractor_id]['cycles'][cycle_id]['cycle'] = payline.cycle
                paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'] = OrderedDict()

            if not finance_code_id in paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes']:
                paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'][finance_code_id] = {}
                paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'][finance_code_id]['finance_code'] = payline.finance_code
                paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'][finance_code_id]['paylines'] = []

            paylines_dict[contractor_id]['cycles'][cycle_id]['finance_codes'][finance_code_id]['paylines'].append(payline)

        unlocked_cycles = Cycle.objects.values('id', 'cycle_date').order_by('-id').filter(locked=False, active=True)
        release_form = CalculationForm(request.GET)
        release_form.fields['c'].widget.choices = to_select(unlocked_cycles, 'id', 'cycle_date', '----------------', 'date')
        release_form.fields['c'].widget.attrs = {'class':'search_release'}


        pp(form.errors)
        return render(request, 'pays/pays/search.html', {'form': form, 'release_form': release_form, 'paylines': paylines_dict, 'config': config, 'query_string': query_string})

@access_required('direct.pays.admin')
def add(request):
    payroll_number = request.POST.get('payroll_number', '')

    if request.method == 'POST':
        form = PaylineForm(request.POST)
        if form.is_valid():
            payline = form.save()
            payline.last_altered_by = request.user.get('username')
            payline.location = payline.contractor.location
            if payline.contractor.pay_gst and payline.gst_value is None:
                payline.gst_value = float(payline.value)/10

            payline.save()

            messages.success(request, 'Payline added successfully.')
            return HttpResponseRedirect(reverse('direct.pays.views.pays.add', args=[request.info.get('current_projectname'),]))
        else:
            messages.error(request, 'Something went wrong.')
    else:
        form = PaylineForm()

    unlocked_cycles = Cycle.objects.values('id', 'cycle_date').order_by('-id').filter(locked=False, active=True)
    locations = Location.objects.values('id', 'location')
    finance_codes = FinanceCode.objects.extra(select={'display': "vcfinance_code+' - '+vcdescription", 'order': "cast(vcfinance_code as int)"}).values('id','display', 'order').extra(order_by=['order'])
    contractors = Contractor.objects.extra(select={'display': "upper(vcIDENTIFIER+' - '+vcNAME)"}).values('id', 'display').filter(referer=False).extra(order_by = ['display'])

    form.fields['cycle'].widget.choices = to_select(unlocked_cycles, 'id', 'cycle_date', None, 'date')
    form.fields['finance_code'].widget.choices = to_select(finance_codes, 'id', 'display', None)
    form.fields['contractor'].widget.choices = to_select(contractors, 'id', 'display', None)
    form.fields['location'].widget.choices = to_select(locations, 'id', 'location', None)

    return render(request, 'pays/pays/add.html', {'form': form, 'payroll_number': payroll_number})

@access_required('direct.pays.admin')
def upload(request):
    if request.method == 'POST':
        cur = connections[request.info.get('current_projectname')+'_pays_default'].cursor()
        cycle_id = request.POST['c']
        failed = []
        paylines = []
        
        _columns = "iCYCLE_ID, iPAY_RUN_ID, bDELETEABLE, bCALCULATED, iFINANCE_CODE_ID, iLOCATION_ID, iUSER_ID, nVALUE, nGST_VALUE, vcDETAILS, iEXTERNAL_RECORD_ID, vcAPPLICATION_ID, vcLAST_ALTERED_BY"
        _place_holders = str(cycle_id)+", 0, 1, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?"

        finance_codes = map_to_key(FinanceCode.objects.values('id', 'finance_code'), 'id')
        locations = map_to_key(Location.objects.values('id', 'location'), 'id')
        contractors = map_to_key(Contractor.objects.values('id', 'name'), 'id')
        
        rows = string.split(request.FILES['file'].read(), "\r\n")
        for row in rows:
            data = string.split(row, ",")
            if len(data) >= 6:
                # file format:
                #
                # finance_code, location, user, value, gst, details, record_id, app_id
                try:
                    payline = []
                    try:
                        finance_codes[int(data[0])]
                    except:
                        raise Exception, 'Finance code id {0} could not be found'.format(data[0])
                    payline.append(int(data[0]))
                    
                    try:
                        locations[int(data[1])]
                    except:
                        raise Exception, 'Location id {0} could not be found'.format(data[1])
                    payline.append(int(data[1]))
                    
                    try:
                        contractors[int(data[2])]
                    except:
                        raise Exception, 'Contractor id {0} could not be found'.format(data[2])
                    payline.append(int(data[2]))
                    
                    payline.append(float(data[3]))
                    payline.append(None)
                    if data[4]:
                        payline[4] = float(data[4])
                    try:
                        data[5].decode('utf-8').encode('utf-8')
                        payline.append(data[5])
                    except:
                        raise Exception, 'Description contains invalid characters'.format(data[5])
                    payline.append(None)
                    if len(data) >= 7:
                        if data[6]:
                            payline[6] = int(data[6])
                    payline.append(None)
                    if len(data) >= 8:
                        payline[7] = data[7]
                    payline.append(request.user.get('username'))
                    paylines.append(payline)
                except Exception, err:
                    data.append(err)
                    failed.append(data)

        sql = 'INSERT INTO [pays].[XTB_Payline] ('+_columns+') values ('+_place_holders+');'
        #cur.execute('begin transaction')
        cur.executemany(sql, paylines)
        cur.execute('commit')
        cur.close()

        if failed:
            failed_file = StringIO()
            writer = csv.writer(failed_file)

            for row in failed:
                writer.writerow(row)

            send_email('Upload failures', 'Failed', [request.user.get('email')], 'pays@salesforce.com.au', [('upload_file.csv', failed_file.getvalue(), 'text/csv')])

        messages.success(request, 'Paylines added successfully. Any failures are being emailed to you.')
        return HttpResponseRedirect(reverse('direct.pays.views.pays.upload', args=[request.info.get('current_projectname'),]))

    unlocked_cycles = Cycle.objects.values('id', 'cycle_date').order_by('-id').filter(locked=False, active=True)
    form = UploadForm()
    form.fields['c'].widget.choices = to_select(unlocked_cycles, 'id', 'cycle_date', None, 'date')

    return render(request, 'pays/pays/upload.html', {'form': form})

@access_required('direct.pays.admin')
def calculate(request, cycle_id):
    #log = logging.getLogger('pays')

    cycle = Cycle.objects.get(pk=cycle_id)
    cycle.calc_date = datetime.datetime.now()
    cycle.save()

    try:
        current_pay_run = PayRun.objects.get(cycle=cycle_id, approved=True)
        current_pay_run.approved = False
        current_pay_run.save()
    except PayRun.DoesNotExist:
        pass

    pay_run = PayRun()
    pay_run.cycle = cycle
    pay_run.created_by = request.user.get('name')
    pay_run.approved_by = request.user.get('name')
    pay_run.approved_date = datetime.datetime.now()
    pay_run.save()

    r = get_redis(db=3)
    id = r.incr('ids:direct.pays')
    data = {'project': request.info.get('current_projectname'), 'cycle': cycle.id, 'pay_run': pay_run.id}
    r.hmset('i:direct.pays:{0}'.format(id), data)
    r.rpush('q:direct.pays', id)

#    mail.send_mail('Run Calculation:'+request.info.get('current_projectname')+' '+str(cycle_id)+':'+str(pay_run.id),
#                    'Run the thing',
#                    'pays@salesforce.com.au',
#                    ['daniel.edgecombe@salmat.com.au'],
#                    fail_silently=False)

    return HttpResponseRedirect(reverse('direct.pays.views.pays.calculating', args=[request.info.get('current_projectname'), cycle_id, pay_run.id]))

@access_required('direct.pays.admin')
def calculating(request, cycle_id, pay_run_id):
    calculation_steps = CalculationStep.objects.all().filter(active=True)

    steps = OrderedDict()
    for cs in calculation_steps:
        if cs.step not in steps:
            steps[cs.step] = {}
            steps[cs.step]['step'] = cs.step_description
            steps[cs.step]['sub_steps'] = OrderedDict()

        steps[cs.step]['sub_steps'][cs.sub_step] = cs.sub_step_description
        
    return render(request, 'pays/pays/calculating.html', {'cycle_id': cycle_id, 'pay_run_id': pay_run_id, 'steps': steps})

@access_required('direct.pays.admin')
def lock(request, cycle_id):
    cycle = Cycle.objects.get(pk=cycle_id)
    cycle.locked = True
    cycle.save()

    #load cycle + 7 days.
    #if new cycle exists do nothing
    #else create cycle + 7

    new_cycle_date = cycle.cycle_date+datetime.timedelta(days=7)
    cycle_exists = Cycle.objects.all().filter(cycle_date=new_cycle_date, active=True)

    if not cycle_exists:
        new_cycle = Cycle()
        new_cycle.cycle_date = cycle.cycle_date+datetime.timedelta(days=7)
        new_cycle.bonus_start_date = cycle.bonus_start_date+datetime.timedelta(days=7)
        new_cycle.bonus_end_date = cycle.bonus_end_date+datetime.timedelta(days=7)
        new_cycle.cancel_start_date = cycle.cancel_start_date+datetime.timedelta(days=7)
        new_cycle.cancel_end_date = cycle.cancel_end_date+datetime.timedelta(days=7)
        new_cycle.locked = False
        new_cycle.save()

    return HttpResponseRedirect(reverse('direct.pays.views.pays.index', args=[request.info.get('current_projectname')]))

@access_required('direct.pays.admin')
def unlock(request, cycle_id):
    cycle = Cycle.objects.get(pk=cycle_id)
    cycle.locked = False
    cycle.save()

    return HttpResponseRedirect(reverse('direct.pays.views.pays.index', args=[request.info.get('current_projectname')])+'?c='+cycle_id)

@access_required('direct.pays.admin')
def held(request):

    messages.info(request, 'Select a cycle to release contractor/cycle/finance code/payline into that cycle.')
    return render(request, 'pays/pays/held.html')

@access_required('direct.pays.admin')
def perm_held(request):

    return render(request, 'pays/pays/perm_held.html')

