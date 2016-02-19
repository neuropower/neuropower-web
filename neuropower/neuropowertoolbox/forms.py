from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML, Fieldset, ButtonHolder
from crispy_forms.bootstrap import PrependedText, PrependedAppendedText, FormActions
from .models import NiftiModel, ParameterModel, PeakTableModel, MixtureModel, PowerTableModel

class NiftiForm(forms.ModelForm):
    class Meta:
        model = NiftiModel
        fields = ['url']
    def __init__(self,*args,**kwargs):
        self.default=kwargs.pop('default',None)
        super(NiftiForm,self).__init__(*args,**kwargs)
        self.fields['url'].widget = forms.URLInput(attrs={'placeholder':self.default})
        self.fields['url'].label = "URL to nifti-file"
        #self.fields['location'].label = "Local link to nifti-file (goal: download URL, store in temp-folder,remove this field)"
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.label_class = 'col-lg-12'
    helper.layout = Layout(
        Fieldset(
            'Data location',
            'url',#'location'
            ),
        HTML("""<br>"""),
        ButtonHolder(Submit('Load', 'Load Image', css_class='btn-secondary'))
    )

class ParameterForm(forms.ModelForm):
    class Meta:
        model = ParameterModel
        fields = ['ZorT','ExcUnits','Exc','Subj','Samples','Smoothx','Smoothy','Smoothz','Voxx','Voxy','Voxz']
    def __init__(self,*args,**kwargs):
        super(ParameterForm,self).__init__(*args,**kwargs)
        self.fields['ZorT'].label = "Are the data Z- or T-values?"
        self.fields['ExcUnits'].label = "What are the units of the screening threshold?"
        self.fields['Exc'].label = "What is the screening threshold?"
        self.fields['Subj'].label = "How many subjects does the group map represent?"
        self.fields['Samples'].label = "Is this a one-sample or a two-sample test?"
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
            'ZorT','ExcUnits','Exc','Subj','Samples'
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
