from django import forms
from django.core import exceptions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML, Fieldset, ButtonHolder
from crispy_forms.bootstrap import PrependedText, PrependedAppendedText, FormActions
from .models import ParameterModel, PeakTableModel, MixtureModel, PowerTableModel,PowerModel

class ParameterForm(forms.ModelForm):
    class Meta:
        model = ParameterModel
        fields = ['url','ZorT','Exc','Subj','Samples','alpha','Smoothx','Smoothy','Smoothz','Voxx','Voxy','Voxz']
    def __init__(self,*args,**kwargs):
        self.default=kwargs.pop('default',None)
        super(ParameterForm,self).__init__(*args,**kwargs)
        self.fields['url'].widget = forms.URLInput(attrs={'placeholder':self.default})
        self.fields['url'].label = "URL to nifti-file"
        self.fields['ZorT'].label = "Are the data Z- or T-values?"
        self.fields['Exc'].label = "What is the screening threshold (either p-value or z-value units)?"
        self.fields['Subj'].label = "How many subjects does the group map represent?"
        self.fields['Samples'].label = "Is this a one-sample or a two-sample test?"
        self.fields['alpha'].label = "At which alpha-level are the statistical tests carried out?"
        self.fields['alpha'].widget = forms.NumberInput(attrs={'placeholder':0.05})

        self.fields['Smoothx'].label = ""
        self.fields['Smoothx'].widget = forms.TextInput(attrs={'placeholder':'x'})
        self.fields['Smoothy'].label = ""
        self.fields['Smoothy'].widget = forms.TextInput(attrs={'placeholder':'y'})
        self.fields['Smoothz'].label = ""
        self.fields['Smoothz'].widget = forms.TextInput(attrs={'placeholder':'z'})
        self.fields['Voxx'].label = ""
        self.fields['Voxx'].widget = forms.TextInput(attrs={'placeholder':'x'})
        self.fields['Voxy'].label = ""
        self.fields['Voxy'].widget = forms.TextInput(attrs={'placeholder':'y'})
        self.fields['Voxz'].label = ""
        self.fields['Voxz'].widget = forms.TextInput(attrs={'placeholder':'z'})
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.label_class = 'col-lg-12'
    helper.layout = Layout(
        Fieldset(
            'Data parameters',
            'url','ZorT','Exc','Subj','Samples','alpha'
            ),
        HTML("""<p style="margin-left: 15px"><b> \n What is the smoothness of the data? </b></p>"""),
        Div(
           Div(Field('Smoothx'), css_class='col-xs-4'),
            Div(Field('Smoothy'), css_class='col-xs-4'),
            Div(Field('Smoothz'), css_class='col-xs-4'),
            css_class='row-xs-12'
        ),
        HTML("""<p style="margin-left: 15px"><b> \n What is the voxel size? </b></p>"""),
        Div(
           Div(Field('Voxx'), css_class='col-xs-4'),
           Div(Field('Voxy'), css_class='col-xs-4'),
           Div(Field('Voxz'), css_class='col-xs-4'),
            css_class='row-xs-12'
        ),
        HTML("""<br><br><br><br><br>"""),
        ButtonHolder(Submit('Submit', 'Submit parameters', css_class='btn-secondary'))
    )

class PeakTableForm(forms.ModelForm):
    class Meta:
        model = PeakTableModel
        fields = '__all__'

class MixtureForm(forms.ModelForm):
    class Meta:
        model = MixtureModel
        fields = '__all__'

class PowerTableForm(forms.ModelForm):
    class Meta:
        model = PowerTableModel
        fields = '__all__'

class PowerForm(forms.ModelForm):
    SID = forms.CharField(required=False)
    reqPow = forms.CharField(required=False,label = "Power")
    reqSS = forms.DecimalField(required=False,label = "Sample size")
    class Meta:
        model = PowerModel
        fields = '__all__'
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.label_class = 'col-lg-12'
    helper.layout = Layout(
        Fieldset(
            'Power',
            HTML("To see the power for a certain sample size or vice versa, please fill out either the minimal power or the sample size."),
            HTML("""<br><br><br>"""),
            'MCP','reqSS','reqPow'
            ),
            HTML("""<br>"""),
            ButtonHolder(Submit('Submit', 'Submit parameters', css_class='btn-secondary'))
    )
    def clean(self):
        super(forms.ModelForm,self).clean()
        reqPow = self.cleaned_data['reqPow']
        reqSS = self.cleaned_data['reqSS']
        if reqPow != '' and reqSS:
            raise exceptions.ValidationError("Please fill out only either the power or the sample size, not both.")
        if reqPow == '':
            self.cleaned_data['reqPow'] = 0
        if not reqSS:
            self.cleaned_data['reqSS'] = 0
        return self.cleaned_data
