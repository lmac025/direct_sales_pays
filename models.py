import datetime
from django.db import models, connections
import django.db.models.options as options
from common.helper_functions import dictfetchall
from pprint import pprint as pp

# Create your models here.
options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('application_name', 'alias')

class CalculationProgress(models.Model):
    ''' * [pays].[LTB_Calculation_Progress]
        * default alias
    '''

    def __unicode__(self):
        return self.step_description

    id = models.AutoField(primary_key=True, db_column='iCALCULATION_PROGRESS_ID')
    pay_run = models.ForeignKey('PayRun', db_column='iPAY_RUN_ID', null=True, default=0)
    cycle = models.ForeignKey('Cycle', db_column='iCYCLE_ID')
    step = models.IntegerField(db_column='iSTEP')
    sub_step = models.IntegerField(db_column='iSUB_STEP')

    class Meta:
        db_table = '[pays].[LTB_Calculation_Progress]'
        application_name = 'pays'
        alias = 'default'
        ordering = ['step','sub_step']
        app_label = 'pays.models'

class CalculationStep(models.Model):
    ''' * [pays].[LTB_Calculation_Step]
        * default alias
    '''

    def __unicode__(self):
        return self.step_description

    id = models.AutoField(primary_key=True, db_column='iCALCULATION_STEP_ID')
    step = models.IntegerField(db_column='iSTEP')
    sub_step = models.IntegerField(db_column='iSUB_STEP')
    step_description = models.CharField(max_length=50, db_column='vcSTEP')
    sub_step_description = models.CharField(max_length=50, db_column='vcSUB_STEP')
    active = models.BooleanField(db_column='bACTIVE', default=True, editable=False)

    class Meta:
        db_table = '[pays].[LTB_Calculation_Step]'
        application_name = 'pays'
        alias = 'default'
        ordering = ['step','sub_step']
        app_label = 'pays.models'

class Config(models.Model):
    ''' * [dbo].[XTB_Config]
        * default alias
    '''

    def __unicode__(self):
        return self.description
        
    id = models.AutoField(primary_key=True, db_column='iCONFIG_ID')
    application = models.CharField(max_length=255, db_column='vcAPPLICATION')
    description = models.CharField(max_length=255, db_column='vcDESCRIPTION')
    logo = models.CharField(max_length=255, db_column='vcLOGO')
    url = models.CharField(max_length=255, db_column='vcEXTERNAL_APP_URL')
    country = models.CharField(max_length=50, db_column='vcCOUNTRY')
    tax_invoice = models.CharField(max_length=50, db_column='vcTAX_INVOICE')
    commission_statement = models.CharField(max_length=50, db_column='vcCOMMISSION_STATEMENT')
    non_standard_tax_invoice = models.CharField(max_length=50, db_column='vcNON_STANDARD_TAX_INVOICE')
    non_standard_commission_statement = models.CharField(max_length=50, db_column='vcNON_STANDARD_COMMISSION_STATEMENT')
    active = models.BooleanField(db_column='bACTIVE')
    
    class Meta:
        db_table = '[dbo].[XTB_Config]'
        application_name = 'pays'
        alias = 'default'
        app_label = 'pays.models'

class Contractor(models.Model):
    ''' * [pays].[XVW_Users]
        * default alias
    '''

    def __unicode__(self):
        return self.name

    id = models.AutoField(primary_key=True, db_column='iUSER_ID')
    name = models.CharField(max_length=255, db_column='vcNAME')
    payroll = models.CharField(max_length=255, db_column='vcPAYROLL_NUMBER')
    sales_code = models.CharField(max_length=255, db_column='vcSALES_CODE')
    abn = models.CharField(max_length=255, db_column='vcABN')
    trading_as = models.CharField(max_length=255, db_column='vcTRADING_AS')
    address = models.CharField(max_length=255, db_column='vcADDRESS')
    suburb = models.CharField(max_length=255, db_column='vcSUBURB')
    role_end = models.DateTimeField(db_column='dROLE_END')
    pay_gst = models.BooleanField(db_column='bPAY_GST')
    referer = models.BooleanField(db_column='bREFERER')
    location = models.ForeignKey('Location', db_column='iLOCATION_ID')
    email = models.CharField(max_length=255, db_column='vcEMAIL')

    class Meta:
        db_table = '[pays].[XVW_Users]'
        application_name = 'pays'
        alias = 'default'
        app_label = 'pays.models'

class CostAccount(models.Model):
    ''' * [pays].[LTB_Cost_Account]
        * default alias
    '''

    def __unicode__(self):
        return self.cost_account

    id = models.AutoField(primary_key=True, db_column='iCOST_ACCOUNT_ID')
    location = models.ForeignKey('Location', db_column='iLOCATION_ID')
    cost_account = models.CharField(max_length=50, db_column='vcCOST_ACCOUNT', verbose_name='Cost Account (4211112222ABC)')
    cost_category_2 = models.CharField(max_length=6, db_column='vcCOST_CATEGORY_2', verbose_name='Cost Account (421111)')
    cost_category_3 = models.CharField(max_length=6, db_column='vcCOST_CATEGORY_3', verbose_name='Cost Account (2222)')
    cost_category_4 = models.CharField(max_length=6, db_column='vcCOST_CATEGORY_4', verbose_name='Cost Account (ABC)')
    active = models.BooleanField(db_column='bACTIVE', default=True, editable=False)
    last_altered = models.DateTimeField(editable=False, auto_now=True, db_column='dLAST_ALTERED')
    last_altered_by = models.CharField(max_length=50, editable=False, db_column='vcLAST_ALTERED_BY')

    class Meta:
        db_table = '[pays].[LTB_Cost_Account]'
        application_name = 'pays'
        alias = 'default'
        ordering = ['location__location',]
        app_label = 'pays.models'

class Cycle(models.Model):
    ''' * [pays].[XTB_Cycle]
        * default alias
    '''

    def __unicode__(self):
        return str(self.id)

    id = models.AutoField(primary_key=True, db_column='iCYCLE_ID')
    calc_date = models.DateTimeField(db_column='dCALCULATION_DATE')
    pay_date = models.DateTimeField(db_column='dPAY_DATE')
    cycle_date = models.DateTimeField(db_column='dCOMM_ENDDATE')
    bonus_start_date = models.DateTimeField(db_column='dBONUS_STARTDATE')
    bonus_end_date = models.DateTimeField(db_column='dBONUS_ENDDATE')
    cancel_start_date = models.DateTimeField(db_column='dBONUS_CANCEL_STARTDATE')
    cancel_end_date = models.DateTimeField(db_column='dBONUS_CANCEL_ENDDATE')
    locked = models.BooleanField(db_column='bLOCKED', default=False)
    active = models.BooleanField(db_column='bACTIVE', default=True)
    
    class Meta:
        db_table = '[pays].[XTB_Cycle]'
        application_name = 'pays'
        alias = 'default'
        app_label = 'pays.models'

class FinanceCode(models.Model):
    ''' * [pays].[LTB_Finance_Code]
        * default alias
    '''

    def __unicode__(self):
        return self.description

    id = models.AutoField(primary_key=True, db_column='iFINANCE_CODE_ID')
    finance_code = models.CharField(max_length=10, db_column='vcFINANCE_CODE')
    aurion_finance_code = models.CharField(max_length=10, db_column='vcAURION_FINANCE_CODE')
    description = models.CharField(max_length=255, db_column='vcDESCRIPTION')
    addition = models.BooleanField(db_column='bADDITION', verbose_name='Aurion Addition code?')
    invoice = models.BooleanField(db_column='bINVOICE', verbose_name='Include in tax invoice?')
    active = models.BooleanField(db_column='bACTIVE', default=True)
    last_altered = models.DateTimeField(editable=False, auto_now=True, db_column='dLAST_ALTERED')
    last_altered_by = models.CharField(max_length=50, editable=False, db_column='vcLAST_ALTERED_BY')

    class Meta:
        db_table = '[pays].[LTB_Finance_Code]'
        application_name = 'pays'
        alias = 'default'
        ordering = ['description',]
        app_label = 'pays.models'

class Location(models.Model):
    ''' * [dbo].[XVW_Location]
        * default alias
    '''

    def __unicode__(self):
        return self.location

    id = models.AutoField(primary_key=True, db_column='iLOCATION_ID')
    location = models.CharField(max_length=255, db_column='vcLOCATION')

    class Meta:
        db_table = '[dbo].[XVW_Location]'
        application_name = 'pays'
        alias = 'default'
        ordering = ['location']
        app_label = 'pays.models'

class Payline(models.Model):
    ''' * [pays].[XTB_Payline]
        * default alias
    '''

    def __unicode__(self):
        return str(self.id)

    id = models.AutoField(primary_key=True, db_column='iPAYLINE_ID')
    #foreign keys
    pay_run = models.ForeignKey('PayRun', db_column='iPAY_RUN_ID', null=True, default=0)
    cycle = models.ForeignKey('Cycle', db_column='iCYCLE_ID')
    finance_code = models.ForeignKey('FinanceCode', db_column='iFINANCE_CODE_ID')
    location = models.ForeignKey('Location', db_column='iLOCATION_ID')
    contractor = models.ForeignKey('Contractor', db_column='iUSER_ID', verbose_name='Payroll Number')
    #bit fields
    manual = models.BooleanField(db_column='bDELETEABLE', default=True)
    held = models.BooleanField(db_column='bHELD', default=False)
    calculated = models.BooleanField(db_column='bCALCULATED', default=False)
    dummy = models.BooleanField(db_column='bDUMMY', default=False)
    perm_held = models.BooleanField(db_column='bPERM_HELD', default=False)
    active = models.BooleanField(db_column='bACTIVE', default=True)
    #payline data
    value = models.FloatField(db_column='nVALUE')
    gst_value = models.FloatField(db_column='nGST_VALUE', null=True, blank=True)
    details = models.TextField(db_column='vcDETAILS')
    grouping = models.CharField(max_length=50, db_column='vcGROUPING')
    reference_payline = models.ForeignKey('self', db_column='iREFERENCE_PAY_ID', null=True)
    external_record_id = models.IntegerField(db_column='iEXTERNAL_RECORD_ID', null=True, blank=True, verbose_name='Pay Id:')
    application_id = models.CharField(max_length=8000, db_column='vcAPPLICATION_ID', null=True, blank=True)
    query_string = models.CharField(max_length=8000, db_column='vcQUERY_STRING')
    #tracking stuff
    last_altered = models.DateTimeField(editable=False, auto_now=True, db_column='dLAST_ALTERED')
    last_altered_by = models.CharField(max_length=50, editable=False, db_column='vcLAST_ALTERED_BY')

    class Meta:
        db_table = '[pays].[XTB_Payline]'
        application_name = 'pays'
        alias = 'default'
        ordering = ['contractor__payroll', '-cycle__id', 'finance_code__description', 'application_id', 'details']
        app_label = 'pays.models'

    @staticmethod
    def payroll_file(cycle_id, project):
        cur = connections[project+'_pays_default'].cursor()
        cur.execute('exec [pays].[XSP_Get_Aurion_Payroll_File] @cycleId=\'{0}\';commit'.format(int(cycle_id)))
        results = dictfetchall(cur)
        cur.close()
        return results

class PayRun(models.Model):
    ''' * [pays].[XTB_Pay_Run]
        * default alias
    '''

    id = models.AutoField(primary_key=True, db_column='iPAY_RUN_ID')
    cycle = models.ForeignKey('Cycle', db_column='iCYCLE_ID')
    created_by = models.CharField(max_length=255, db_column='vcCREATED_BY')
    created_date = models.DateTimeField(db_column='dCREATED', auto_now_add=True)
    approved = models.BooleanField(db_column='bAPPROVED', default=True)
    approved_by = models.CharField(max_length=255, db_column='vcAPPROVED_BY')
    approved_date = models.DateTimeField(db_column='dAPPROVED', auto_now_add=True)
    exported = models.BooleanField(db_column='bEXPORTED', default=True)
    exported_by = models.CharField(max_length=255, db_column='vcEXPORTED_BY')
    exported_date = models.DateTimeField(db_column='dEXPORTED')
    failed = models.BooleanField(db_column='bFAILED', default=False)
    calculated = models.BooleanField(db_column='bCALCULATED', default=False)
    exported = models.BooleanField(db_column='bEXPORTED', default=False)
    active = models.BooleanField(db_column='bACTIVE', default=True)

    class Meta:
        db_table = '[pays].[XTB_Pay_Run]'
        application_name = 'pays'
        alias = 'default'
        app_label = 'pays.models'

