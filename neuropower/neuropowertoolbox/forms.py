from django import forms
from django.core import exceptions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML, Fieldset, ButtonHolder
from crispy_forms.bootstrap import PrependedText, PrependedAppendedText, FormActions
from .models import ParameterModel, PeakTableModel, MixtureModel, PowerTableModel,PowerModel
import nibabel as nib

class ParameterForm(forms.ModelForm):
    class Meta:
        model = ParameterModel
        fields = ['url','maskfile','ZorT','Exc','Subj','Samples','alpha','Smoothx','Smoothy','Smoothz','Voxx','Voxy','Voxz']
    def __init__(self,*args,**kwargs):
        self.default_url=kwargs.pop('default_url')
        self.dim_err=kwargs.pop('dim_err')
        super(ParameterForm,self).__init__(*args,**kwargs)
        self.fields['url'].widget = forms.URLInput(attrs={'placeholder':self.default_url})
        self.fields['url'].label = "URL to nifti-file"
        self.fields['maskfile'].label = "Upload a full brain mask or a Region-of-Interest mask.  If no mask is selected, all non-null voxels are used."
        self.fields['maskfile'].required = False
        self.fields['ZorT'].label = "Are the data Z- or T-values?"
        self.fields['Exc'].label = "What is the screening threshold (either p-value or z-value units)?"
        self.fields['Subj'].label = "How many subjects does the group map represent?"
        self.fields['Samples'].label = "Is this a one-sample or a two-sample test?"
        self.fields['alpha'].label = "At which alpha-level are the statistical tests carried out?"
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
    def clean(self):
        cleaned_data = super(ParameterForm,self).clean()
        url = cleaned_data.get('url')
        maskfile = cleaned_data.get('maskfile')
        exc = cleaned_data.get('Exc')
        subj = cleaned_data.get("Subj")
        alpha = cleaned_data.get("alpha")
        if self.dim_err:
            raise forms.ValidationError("The selected statistical map and mask do not have the same dimensions.")
        if not (url.endswith('.nii.gz') or url.endswith('.nii.gz')):
            raise forms.ValidationError("The statistical map has the wrong format: please choose a nifti-file")
        if not maskfile == None:
            if not (maskfile.name.endswith('.nii.gz') or maskfile.name.endswith('.nii.gz')):
                raise forms.ValidationError("The mask has the wrong format: please choose a nifti-file")
            if maskfile.size > 10^7:
                raise forms.ValidationError("Maximum mask file size: 10 MB")
        if 0.5 < exc < 2:
            raise forms.ValidationError("For a p-value, that screening threshold is too big; for a t-value it's too small.")
        if exc > 5:
            raise forms.ValidationError("Your screening threshold is impossibly high.")
        if subj < 10:
            raise forms.ValidationError("We found that our power estimations are not valid for sample sizes smaller than 10!")
        if alpha > 0.20:
            raise forms.ValidationError("Are you sure about that alpha level? Your tests have a high chance of producing false positives.")
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.label_class = 'col-lg-12'
    helper.layout = Layout(
        Fieldset(
            'Data parameters',
            'url','maskfile','ZorT','Exc','Subj','Samples','alpha'
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
