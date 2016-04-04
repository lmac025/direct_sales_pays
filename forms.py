# Create your views here.
import inspect, datetime, csv
from django import forms
from direct.pays.models import *

from pprint import pprint as pp
            
class CalculationForm(forms.Form):
    c = forms.ChoiceField(label='Cycle:')
    l = forms.ChoiceField(label='Location:')

class PaylineForm(forms.ModelForm):
    class Meta:
        model = Payline
        exclude = ('reference_payline','pay_run', 'query_string', 'grouping', 'perm_held', 'dummy', 'calculated', 'held', 'active', 'manual')

    def __init__(self, *args, **kwargs):
        super(PaylineForm, self).__init__(*args, **kwargs) # Call to ModelForm constructor
        self.fields['details'].widget.attrs['cols'] = 50
        self.fields['details'].widget.attrs['rows'] = 5
        self.fields['cycle'].widget = forms.Select()
        self.fields['contractor'].widget = forms.HiddenInput()
        self.fields['finance_code'].widget = forms.Select()

class UploadForm(forms.Form):
    c = forms.ChoiceField(label='Cycle:')
    file = forms.FileField()

class SearchForm(forms.Form):
    cycle = forms.ChoiceField(required=False)
    location = forms.ChoiceField(required=False)
    finance_code = forms.ChoiceField(required=False)
    payroll = forms.IntegerField(label='Payroll Number', required=False)
    sales_code = forms.CharField(label='Sales Code', required=False)
    application_id = forms.CharField(required=False)
    pay_id = forms.IntegerField(label='Pay Id', required=False)

class FinanceCodeForm(forms.ModelForm):
    class Meta:
        model = FinanceCode
        exclude = ('active')

class CostAccountForm(forms.ModelForm):
    class Meta:
        model = CostAccount
        exclude = ('active')
