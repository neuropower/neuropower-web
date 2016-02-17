from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML
from crispy_forms.bootstrap import PrependedText, PrependedAppendedText, FormActions
from .models import NiftiModel, ParameterModel

class NiftiForm(forms.ModelForm):
    class Meta:
        model = NiftiModel
        fields = '__all__'
    def __init__(self,*args,**kwargs):
        self.default=kwargs.pop('default',None)
        super(NiftiForm,self).__init__(*args,**kwargs)
        self.fields['url'].widget = forms.URLInput(attrs={'placeholder':self.default})
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.label_class = 'col-lg-12'
    helper.layout = Layout(
        'url','location',
        helper.add_input(Submit('Load', 'Load Image', css_class='btn-secondary'))
    )

class ParameterForm(forms.ModelForm):
    class Meta:
        model = ParameterModel
        fields = '__all__'
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.label_class = 'col-lg-12'
    helper.layout = Layout(
        'ZorT',
        'ExcUnits',
        'Exc',
        'Subj',
        'Samples',
        HTML("""
        <p style="margin-left: 15px"><b> \n What is the smoothness of the data? </b></p>
        """),
        Div(
           Div(Field('Smoothx'), css_class='col-xs-4'),
            Div(Field('Smoothy'), css_class='col-xs-4'),
            Div(Field('Smoothz'), css_class='col-xs-4'),
            css_class='row-xs-12'
        ),
        HTML("""
        <p style="margin-left: 15px"><b> \n What is the voxel size? </b></p>
        """),
        Div(
           Div(Field('Voxx'), css_class='col-xs-4'),
           Div(Field('Voxy'), css_class='col-xs-4'),
           Div(Field('Voxz'), css_class='col-xs-4'),
            css_class='row-xs-12'
        ),
    helper.add_input(Submit('Submit', 'Submit', css_class='btn-secondary'))
    )
