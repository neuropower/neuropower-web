from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML
from crispy_forms.bootstrap import PrependedText, PrependedAppendedText, FormActions
from .models import NiftiModel

class NiftiForm(forms.ModelForm):
    class Meta:
        model = NiftiModel
        fields = '__all__'
    def __init__(self,*args,**kwargs):
        self.default=kwargs.pop('default',None)
        super(NiftiForm,self).__init__(*args,**kwargs)
        self.fields['file'].widget = forms.URLInput(attrs={'placeholder':self.default})
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.label_class = 'col-lg-12'
    helper.layout = Layout(
        'file',
    helper.add_input(Submit('Load', 'Load Image', css_class='btn-secondary'))
        )

class ParameterForm(forms.Form):
    ZorT_c = ((1,"Z"),(2,"T"))
    ZorT = forms.TypedChoiceField(
        label="Are the values Z- or T-values?",
        required=True,
        choices=ZorT_c
        )
    ExcUnits_c = ((1,"units = p-values (SPM default)"),(2,"units = t-values (FSL default)"))
    ExcUnits = forms.ChoiceField(
        label="What are the units of your filtering threshold?",
        required=True,
        choices=ExcUnits_c
        )
    Exc = forms.DecimalField(
        label="What is your filtering threshold?",
        required=True
        )
    Subj = forms.IntegerField(
        label="How many subjects does the pilot data contain?",
        required=True
        )
    Samples_c = (
        (1, ("One-sample")),
        (2, ("Two-sample"))
        )
    Samples = forms.ChoiceField(
        label="Is the study a one- or two-sample test",
        choices=Samples_c
        )
    Smoothx = forms.CharField(label="",widget=forms.TextInput(attrs={'placeholder':'x'}))
    Smoothy = forms.CharField(label="",widget=forms.TextInput(attrs={'placeholder':'y'}))
    Smoothz = forms.CharField(label="",widget=forms.TextInput(attrs={'placeholder':'z'}))
    Voxx = forms.CharField(label="",widget=forms.TextInput(attrs={'placeholder':'x'}))
    Voxy = forms.CharField(label="",widget=forms.TextInput(attrs={'placeholder':'y'}))
    Voxz = forms.CharField(label="",widget=forms.TextInput(attrs={'placeholder':'z'}))

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
