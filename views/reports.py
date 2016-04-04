# Create your views here.
import inspect, datetime, csv
import os, errno

from pprint import pprint as pp

from collections import OrderedDict

from django.conf import settings
from django.contrib import messages
from django.core import mail
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from common.decorators import access_required
from direct.pays.models import *
from direct.pays.forms import *

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.units import inch

@access_required('direct.pays.admin')
def held(request):
    location = request.GET.get('l')

    head_row = (
        "Location", "Sales Code", "Payroll", "Contractor", "Cycle Date", "Finance Code",
        "Details", "Amount", "GST", "Application Id"
    )

    held_paylines = Payline.objects.select_related().all().filter(Q(pay_run__approved=True) | Q(pay_run=0), cycle__locked=True, active=True, dummy=False, perm_held=False, held=True, reference_payline=None)
    # cur = connections[request.info.get('current_projectname')+'_pays_default'].cursor()
    # sql = '''
    #     select  location        =   l.vclocation,
    #             user_id         =   pl.iuser_id,
    #             cycle_date      =   c.dcomm_enddate,
    #             fc_description  =   fc.vcdescription,
    #             details         =   pl.vcdetails,
    #             value           =   pl.nvalue,
    #             gst_value       =   pl.ngst_value,
    #             application_id  =   pl.vcapplication_id
    #     from    pays.xtb_payline pl
    #     join    pays.ltb_finance_code fc
    #             on fc.ifinance_code_id = pl.ifinance_code_id
    #     join    dbo.xvw_location l
    #             on l.ilocation_id = pl.ilocation_id
    #     join    pays.xtb_cycle c
    #             on c.icycle_id = pl.icycle_id
    #             and c.blocked = 1
    #     join    pays.xtb_pay_run pr
    #             on pr.icycle_id = pl.icycle_id
    #             and pr.bapproved = 1
    #             and (pr.ipay_run_id = pl.ipay_run_id or pl.ipay_run_id = 0)
    #     where   pl.bactive = 1
    #             and pl.bdummy = 0
    #             and pl.bheld = 1
    #             and pl.bperm_held = 0
    #             and pl.ireference_pay_id is null

    # '''
    # cur.execute(sql)
    # results = dictfetchall(cur)
    # cur.close()
   
    filename = datetime.datetime.now().strftime('%Y-%m-%d')
    if location:
        held_paylines = held_paylines.filter(location=location)
        location = Location.objects.get(pk=location)
        filename = filename + ' ' + location.location

    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename='+filename+' Held Pays.csv'

    xstr = lambda s: s or ""
    
    writer = csv.writer(response, quoting=csv.QUOTE_ALL)
    writer.writerow(head_row)
    for payline in held_paylines:
        row = (payline.location, payline.contractor.sales_code, payline.contractor.payroll, payline.contractor.name,
                payline.cycle.cycle_date, payline.finance_code.description,
                xstr(payline.details).encode('utf8'), payline.value, payline.gst_value, payline.application_id)
        # id = payline.get('application_id') or ''
        # row = (payline.get('location'), '', '', '',
        #         payline.get('cycle_date'), payline.get('fc_description'),
        #         xstr(payline.get('details')).encode('utf8'), payline.get('value'), payline.get('gst_value'), '="'+id+'"')
        writer.writerow(row)

    return response

@access_required('direct.pays.access')
def paylines(request, cycle_id):
    location = request.GET.get('l')

    head_row = (
        "Finance Code", "Location", "Contractor Id", "Sales Code", "Contractor", "Payroll",
        "Amount", "GST", "Details", "Joker Id", "Application Id", "Cycle", "Held"
    )

    pay_run = PayRun.objects.get(cycle=cycle_id, approved=True)
    cycle = Cycle.objects.get(pk=cycle_id)

    paylines = Payline.objects.select_related().all().filter(Q(pay_run=pay_run) | Q(pay_run=0), cycle=cycle_id, active=True, dummy=False, perm_held=False, reference_payline=None).order_by('location', 'contractor__name')

    filename = cycle.cycle_date.strftime('%Y-%m-%d')
    if location:
        paylines = paylines.filter(location=location)
        location = Location.objects.get(pk=location)
        filename = filename + ' ' + location.location

    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename='+filename+' Payline Extract.csv'

    xstr = lambda s: s or ""

    writer = csv.writer(response, quoting=csv.QUOTE_ALL)
    writer.writerow(head_row)
    for payline in paylines:
        row = (payline.finance_code.description, payline.location, payline.contractor.id, payline.contractor.sales_code,
                payline.contractor.name, payline.contractor.payroll, payline.value, payline.gst_value,
                xstr(payline.details).encode('utf8'),
                payline.external_record_id, payline.application_id, payline.cycle.cycle_date, payline.held)
        writer.writerow(row)

    return response

@access_required('direct.pays.admin')
def payline_summary(request, cycle_id):
    location = request.GET.get('l')

    head_row = (
        "Contractor Name", "Payroll", "Sales Code", "Location", "Finance Code", "Grouping", "Amount", "GST", "Count","Held"
    )

    pay_run = PayRun.objects.get(cycle=cycle_id, approved=True)
    cycle = Cycle.objects.get(pk=cycle_id)

    paylines = Payline.objects.select_related().all().filter(Q(pay_run=pay_run) | Q(pay_run=0), cycle=cycle_id, active=True, dummy=False, perm_held=False, reference_payline=None).order_by('location', 'contractor__name')

    filename = cycle.cycle_date.strftime('%Y-%m-%d')

    if location:
        paylines = paylines.filter(location=location)
        location = Location.objects.get(pk=location)
        filename = filename + ' ' + location.location

    paylines_dict = OrderedDict()

    for payline in paylines:
        contractor_id = payline.contractor.id
        finance_code_id = payline.finance_code.id
        grouping = payline.grouping
        if not contractor_id in paylines_dict:
            paylines_dict[contractor_id] = {}
            paylines_dict[contractor_id]['contractor'] = payline.contractor
            paylines_dict[contractor_id]['location'] = payline.location
            paylines_dict[contractor_id]['finance_codes'] = OrderedDict()
        if not finance_code_id in paylines_dict[contractor_id]['finance_codes']:
            paylines_dict[contractor_id]['finance_codes'][finance_code_id] = {}
            paylines_dict[contractor_id]['finance_codes'][finance_code_id]['finance_code'] = payline.finance_code
            paylines_dict[contractor_id]['finance_codes'][finance_code_id]['active_groupings'] = OrderedDict()
            paylines_dict[contractor_id]['finance_codes'][finance_code_id]['held_groupings'] = OrderedDict()
        
        if not payline.held:
            if not grouping in paylines_dict[contractor_id]['finance_codes'][finance_code_id]['active_groupings']:
                paylines_dict[contractor_id]['finance_codes'][finance_code_id]['active_groupings'][grouping] = {}
                paylines_dict[contractor_id]['finance_codes'][finance_code_id]['active_groupings'][grouping]['total'] = 0
                paylines_dict[contractor_id]['finance_codes'][finance_code_id]['active_groupings'][grouping]['total_gst'] = 0
                paylines_dict[contractor_id]['finance_codes'][finance_code_id]['active_groupings'][grouping]['count'] = 0

            paylines_dict[contractor_id]['finance_codes'][finance_code_id]['active_groupings'][grouping]['total'] += payline.value
            paylines_dict[contractor_id]['finance_codes'][finance_code_id]['active_groupings'][grouping]['total_gst'] += float(payline.gst_value or 0)
            paylines_dict[contractor_id]['finance_codes'][finance_code_id]['active_groupings'][grouping]['count'] += 1
        else:
            if not grouping in paylines_dict[contractor_id]['finance_codes'][finance_code_id]['held_groupings']:
                paylines_dict[contractor_id]['finance_codes'][finance_code_id]['held_groupings'][grouping] = {}
                paylines_dict[contractor_id]['finance_codes'][finance_code_id]['held_groupings'][grouping]['total'] = 0
                paylines_dict[contractor_id]['finance_codes'][finance_code_id]['held_groupings'][grouping]['total_gst'] = 0
                paylines_dict[contractor_id]['finance_codes'][finance_code_id]['held_groupings'][grouping]['count'] = 0

            paylines_dict[contractor_id]['finance_codes'][finance_code_id]['held_groupings'][grouping]['total'] += payline.value
            paylines_dict[contractor_id]['finance_codes'][finance_code_id]['held_groupings'][grouping]['total_gst'] += float(payline.gst_value or 0)
            paylines_dict[contractor_id]['finance_codes'][finance_code_id]['held_groupings'][grouping]['count'] += 1


    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename='+filename+' Payline Summary.csv'

    writer = csv.writer(response, quoting=csv.QUOTE_ALL)
    writer.writerow(head_row)
    for contractor_id, contractor_data in paylines_dict.items():
        contractor = contractor_data['contractor']
        for finance_code_id, finance_code_data in contractor_data['finance_codes'].items():
            for grouping, grouping_data in finance_code_data['active_groupings'].items():
                row = (contractor.name, contractor.payroll, contractor.sales_code, contractor_data['location'], finance_code_data['finance_code'].description,
                        grouping, grouping_data.get('total'), grouping_data.get('total_gst'), grouping_data.get('count'),'No')
                writer.writerow(row)
            for grouping, grouping_data in finance_code_data['held_groupings'].items():
                row = (contractor.name, contractor.payroll, contractor.sales_code, contractor_data['location'], finance_code_data['finance_code'].description,
                        grouping, grouping_data.get('total'), grouping_data.get('total_gst'), grouping_data.get('count'),'Yes')
                writer.writerow(row)


    return response

@access_required('direct.pays.admin')
def payroll_files(request, cycle_id):
    location = request.GET.get('l')

    data = Payline.payroll_file(cycle_id, request.info.get('current_projectname'))

    pay_run = PayRun.objects.get(cycle=cycle_id, approved=True)
    pay_run.exported = True
    pay_run.exported_by = request.user.get('name')
    pay_run.exported_date = datetime.datetime.now()
    pay_run.save()

    cycle = Cycle.objects.get(pk=cycle_id)
    d = cycle.calc_date
    # 3 is thursday.weekday. so difference from thursday to calc day added to calc day gives thursday
    cycle.pay_date = d + datetime.timedelta(3 - d.weekday())
    cycle.save()

    aurion_file = '/mnt/direct/pays/aurion/'+request.info.get('current_projectname')+'_aurion.csv'
    af = open(aurion_file, 'w+')

    writer = csv.writer(af, quoting=csv.QUOTE_ALL)

    for d in data:
        if d.get('descr') == 'PAYROLL_TS_ADDD':
            row = (d.get('descr'), d.get('payroll'), d.get('finance_code'), d.get('col1'))
        if d.get('descr') == 'PAYROLL_TS_PRO':
            row = (d.get('descr'), d.get('payroll'))
        else:
            row = (d.get('descr'), d.get('payroll'), d.get('finance_code'), d.get('col1'), d.get('col2'), d.get('comm_amount'), d.get('aurion_date')
                    , d.get('col3'), d.get('cost_category_1'), d.get('cost_category_2'), d.get('cost_category_3'), d.get('cost_category_4'))
        writer.writerow(row)

    messages.success(request, 'Aurion file generated and saved to the Direct Sales PMA folder.')
    return HttpResponseRedirect(reverse('direct.pays.views.pays.index', args=[request.info.get('current_projectname'),]))

@access_required('direct.pays.admin')
def commission_statements(request, cycle_id):
    location = request.GET.get('l')

    config = Config.objects.get(application='pays')
    cycle = Cycle.objects.get(pk=cycle_id)
    contractor = request.GET.get('contractor')

    pay_run = PayRun.objects.get(cycle=cycle_id, approved=True)
    paylines = Payline.objects.select_related().all().filter(Q(pay_run=pay_run.id) | Q(pay_run=0), cycle=cycle_id, active=True, dummy=False, held=False, perm_held=False)

    if location:
        paylines = paylines.filter(location=location)

    if contractor:
        paylines = paylines.filter(contractor=contractor)

    paylines_dict = OrderedDict()

    for payline in paylines:
        contractor_id = payline.contractor.id
        location_id = payline.location.id
        if not location_id in paylines_dict:
            paylines_dict[location_id] = {}
            paylines_dict[location_id]['location'] = payline.location
            paylines_dict[location_id]['contractors'] = OrderedDict()
        if not contractor_id in paylines_dict[location_id]['contractors']:
            paylines_dict[location_id]['contractors'][contractor_id] = {}
            paylines_dict[location_id]['contractors'][contractor_id]['contractor'] = payline.contractor
            paylines_dict[location_id]['contractors'][contractor_id]['paylines'] = []

        paylines_dict[location_id]['contractors'][contractor_id]['paylines'].append(payline)

    base_folder = '/mnt/direct/pays/pdfs/Commission Statements/'+request.info.get('current_projectname')+'/'+cycle.pay_date.strftime('%Y%m%d')
    for location_id, location_data in paylines_dict.items():
        if config.commission_statement == 'Multiple' or contractor:
            folder = base_folder+'/'+location_data['location'].location
            check_folder(folder)

            for contractor_id, contractor_data in location_data['contractors'].items():
                pdf_file = folder+'/'+contractor_data['contractor'].name+'.pdf'
                pdf = open(pdf_file, 'w+')

                p=canvas.Canvas(pdf,pagesize=portrait(A4), bottomup=0)

                render_contractor(p, contractor_data, cycle, config.logo, 'Commission Statement')

                p.save()

                if contractor_data.get('contractor').email:
                    ##Generate the file in a buffer and email.
                    ## email.attach_file(pdf_file) seems to send it corrupted. this doesnt.
                    buffer = StringIO()

                    p_email = canvas.Canvas(buffer,pagesize=portrait(A4), bottomup=0)

                    render_contractor(p_email, contractor_data, cycle, config.logo, 'Commission Statement')

                    p_email.save()
                    pdf_email = buffer.getvalue()
                    buffer.close()

                    email = mail.EmailMessage('{0} commission statement: {1}'.format(request.info.get('current_formal_projectname'), cycle.pay_date.strftime('%d-%m-%Y')),
                                            '''Please find attached your commission statement.
Keep this in a safe place. Replacing a lost Commission Statement will result in a fee.''', 
                                            'pays@salesforce.com.au', [contractor_data.get('contractor').email])
                    email.attach(contractor_data['contractor'].name+'.pdf', pdf_email, 'application/pdf')
                    email.send()

        else:
            folder = base_folder
            check_folder(folder)

            pdf_file = folder+'/'+location_data['location'].location+'.pdf'
            pdf = open(pdf_file, 'w+')
            p=canvas.Canvas(pdf,pagesize=portrait(A4), bottomup=0)

            for contractor_id, contractor_data in location_data['contractors'].items():
                render_contractor(p, contractor_data, cycle, config.logo, 'Commission Statement')

                if contractor_data.get('contractor').email:
                    ##Generate the file in a buffer and email.
                    ## email.attach_file(pdf_file) seems to send it corrupted. this doesnt.
                    buffer = StringIO()

                    p_email = canvas.Canvas(buffer,pagesize=portrait(A4), bottomup=0)

                    render_contractor(p_email, contractor_data, cycle, config.logo, 'Commission Statement')

                    p_email.save()
                    pdf_email = buffer.getvalue()
                    buffer.close()

                    email = mail.EmailMessage('{0} commission statement: {1}'.format(request.info.get('current_formal_projectname'), cycle.pay_date.strftime('%d-%m-%Y')),
                                            '''Please find attached your commission statement.
Keep this in a safe place. Replacing a lost Commission Statement will result in a fee.''', 
                                            'pays@salesforce.com.au', [contractor_data.get('contractor').email])
                    email.attach(contractor_data['contractor'].name+'.pdf', pdf_email, 'application/pdf')
                    email.send()

            p.save()

    messages.success(request, 'Commission Statements generated and saved to the Direct Sales Commission Statement folder.')
    return HttpResponseRedirect(reverse('direct.pays.views.pays.index', args=[request.info.get('current_projectname'),])+'?c='+str(cycle_id))

@access_required('direct.pays.admin')
def tax_invoices(request, cycle_id):
    location = request.GET.get('l')

    config = Config.objects.get(application='pays')
    cycle = Cycle.objects.get(pk=cycle_id)

    pay_run = PayRun.objects.get(cycle=cycle_id, approved=True)
    paylines = Payline.objects.select_related().all().filter(Q(pay_run=pay_run.id) | Q(pay_run=0), cycle=cycle_id, finance_code__invoice=True, active=True, dummy=False, held=False, perm_held=False)

    if location:
        paylines = paylines.filter(location=location)
    
    paylines_dict = OrderedDict()

    for payline in paylines:
        contractor_id = payline.contractor.id
        location_id = payline.location.id
        finance_code_id = payline.finance_code.id
        if not location_id in paylines_dict:
            paylines_dict[location_id] = {}
            paylines_dict[location_id]['location'] = payline.location
            paylines_dict[location_id]['contractors'] = OrderedDict()
        if not contractor_id in paylines_dict[location_id]['contractors']:
            paylines_dict[location_id]['contractors'][contractor_id] = {}
            paylines_dict[location_id]['contractors'][contractor_id]['contractor'] = payline.contractor
            paylines_dict[location_id]['contractors'][contractor_id]['finance_codes'] = OrderedDict()
        if not finance_code_id in paylines_dict[location_id]['contractors'][contractor_id]['finance_codes']:
            paylines_dict[location_id]['contractors'][contractor_id]['finance_codes'][finance_code_id] = {}
            paylines_dict[location_id]['contractors'][contractor_id]['finance_codes'][finance_code_id]['finance_code'] = payline.finance_code
            paylines_dict[location_id]['contractors'][contractor_id]['finance_codes'][finance_code_id]['total'] = 0

        paylines_dict[location_id]['contractors'][contractor_id]['finance_codes'][finance_code_id]['total'] += payline.value

    base_folder = '/mnt/direct/pays/pdfs/Tax Invoices/'+request.info.get('current_projectname')+'/'+cycle.pay_date.strftime('%Y%m%d')
    for location_id, location_data in paylines_dict.items():
        if config.tax_invoice == 'Multiple':
            folder = base_folder+'/'+location_data['location'].location
            check_folder(folder)

            for contractor_id, contractor_data in location_data['contractors'].items():
                pdf_file = folder+'/'+contractor_data['contractor'].name+'.pdf'
                pdf = open(pdf_file, 'w+')
                p=canvas.Canvas(pdf,pagesize=portrait(A4), bottomup=0)

                render_contractor(p, contractor_data, cycle, config.logo, 'Tax Invoice')

                p.save()
        else:
            folder = base_folder
            check_folder(folder)

            pdf_file = folder+'/'+location_data['location'].location+'.pdf'
            pdf = open(pdf_file, 'w+')
            p=canvas.Canvas(pdf,pagesize=portrait(A4), bottomup=0)

            for contractor_id, contractor_data in location_data['contractors'].items():
                render_contractor(p, contractor_data, cycle, config.logo, 'Tax Invoice')

            p.save()

    messages.success(request, 'Tax Invoices generated and saved to the Direct Sales Tax Invoice folder.')
    return HttpResponseRedirect(reverse('direct.pays.views.pays.index', args=[request.info.get('current_projectname'),])+'?c='+str(cycle_id))

def check_folder(folder):
    try:
        os.makedirs(folder)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise

def render_contractor(pdf, contractor_data, cycle, logo, statement_type):
    render_header(pdf, contractor_data['contractor'], cycle, logo, statement_type)
    if statement_type == "Commission Statement":
        render_paylines(pdf, contractor_data['paylines'])

    else:
        render_summary(pdf, contractor_data['finance_codes'])

    render_footer(pdf)
    pdf.showPage()

def render_header(pdf, contractor, cycle, logo, statement_type):
    x = 300
    y = 35
    pdf.setFont("Helvetica", 15)
    if statement_type == 'Commission Statement':
        pdf.drawCentredString(x, y, 'Commission Statement')
    else:
        pdf.drawCentredString(x, y, 'Tax Invoice')
        pdf.setFont("Helvetica", 8)
        pdf.drawCentredString(x, y+10, 'please retain for tax purposes as reprints will incur a fee')

    pdf.drawImage(settings.STATIC_ROOT+'direct/images/pays/logos/'+logo, x-300, y+30, height=30, preserveAspectRatio=True)
    pdf.drawImage(settings.STATIC_ROOT+'direct/images/pays/logos/salmat_logo.jpg', x+120, y+30, height=30, preserveAspectRatio=True)

    x = 150
    y = 60
    pdf.setFont("Helvetica", 6)
    pdf.drawString(x, y, 'Salesforce Australia Pty. Ltd.')
    pdf.drawString(x, y+10, '50 Franklin St')
    pdf.drawString(x, y+20, 'Melbourne 3000')
    pdf.drawString(x, y+30, 'VIC, Australia')
    pdf.drawString(x, y+40, 'ABN: 30 006 688 955')

    x = 50
    y = 120
    pdf.setFont("Helvetica", 8)
    pdf.drawString(x, y+10, 'Name:')
    pdf.drawString(x+100, y+10, contractor.name)
    pdf.drawString(x, y+20, 'Trading As:')
    pdf.drawString(x+100, y+20, contractor.trading_as)
    pdf.drawString(x, y+30, 'Address:')
    pdf.drawString(x+100, y+30, contractor.address)
    pdf.drawString(x+100, y+40, contractor.suburb)
    pdf.drawString(x, y+50, 'Sales Code:')
    pdf.drawString(x+100, y+50, contractor.sales_code)
    pdf.drawString(x, y+60, 'Payroll:')
    pdf.drawString(x+100, y+60, contractor.payroll)
    pdf.drawString(x, y+70, 'Pay Date:')
    pdf.drawString(x+100, y+70, cycle.pay_date.strftime('%d-%b-%Y'))
    pdf.drawString(x, y+80, 'Commission Date:')
    pdf.drawString(x+100, y+80, cycle.cycle_date.strftime('%d-%b-%Y'))
    pdf.drawString(x, y+90, 'Bonus Dates:')
    pdf.drawString(x+100, y+90, cycle.bonus_start_date.strftime('%d-%b-%Y')+' to '+cycle.bonus_end_date.strftime('%d-%b-%Y'))
    pdf.drawString(x, y+100, 'Cancel Dates:')
    pdf.drawString(x+100, y+100, cycle.cancel_start_date.strftime('%d-%b-%Y')+' to '+cycle.cancel_end_date.strftime('%d-%b-%Y'))
    pdf.drawString(x, y+110, 'ABN:')
    pdf.drawString(x+100, y+110, contractor.abn)

def render_paylines(pdf, paylines):
    x = 50
    y = 270
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(x, y, 'Details')
    pdf.drawString(x+300, y, 'Payment Type')
    pdf.drawString(x+450, y, 'Amount')
    total = 0
    for payline in paylines:
        if y > 770:
            y = 50
            render_footer(pdf)
            pdf.showPage()

        pdf.setFont("Helvetica", 8)
        detail_chunks = chunks(payline.details, 70)
        key=0
        for key, chunk in enumerate(detail_chunks):
            pdf.drawString(x, y+15+(key*10), chunk)

        pdf.drawString(x+300, y+15, payline.finance_code.description)
        pdf.drawString(x+450, y+15, '$'+str(payline.value))
        total += payline.value

        y += 15+(key*10)

    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(x+300, y+20, 'Total')
    pdf.drawString(x+450, y+20, '$'+str(total))

def render_summary(pdf, finance_codes):
    x = 50
    y = 270
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(x, y, 'Payment Type')
    pdf.drawString(x+450, y, 'Amount')
    total = 0
    for finance_code_id, finance_code_data in finance_codes.items():
        if y > 770:
            y = 50
            render_footer(pdf)
            pdf.showPage()

        pdf.setFont("Helvetica", 8)
        pdf.drawString(x, y+15, finance_code_data['finance_code'].description)
        pdf.drawString(x+450, y+15, '$'+str(finance_code_data['total']))
        total += finance_code_data['total']

        y += 15

    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(x+300, y+20, 'Total')
    pdf.drawString(x+450, y+20, '$'+str(total))

def render_footer(pdf):
    pdf.setFont("Helvetica-Oblique", 8)
    pdf.drawCentredString(300, 820, 'All payments on this statement exclude GST')
    pdf.drawCentredString(300, 830, 'Pg. %d' % pdf.getPageNumber())

def chunks(s, n):
    """Produce `n`-character chunks from `s`."""
    temp = []
    if s:
        for start in range(0, len(s), n):
            temp.append(s[start:start+n])

    return temp
