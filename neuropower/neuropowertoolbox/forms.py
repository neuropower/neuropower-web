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
        fields = ['url','spmfile','maskfile','ZorT','Exc','Subj','Samples','alpha','Smoothx','Smoothy','Smoothz','Voxx','Voxy','Voxz']
    def __init__(self,*args,**kwargs):
        self.default_url=kwargs.pop('default_url')
        self.err=kwargs.pop('err')
        super(ParameterForm,self).__init__(*args,**kwargs)
        self.fields['url'].widget = forms.URLInput(attrs={'placeholder':self.default_url})
        self.fields['url'].label = "URL"
        self.fields['url'].required = False
        self.fields['spmfile'].label = "Upload"
        self.fields['spmfile'].required = False
        #self.fields['maskfile'].label = "Upload a full brain mask or a Region-of-Interest mask."
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
        spmfile = cleaned_data.get('spmfile')
        maskfile = cleaned_data.get('maskfile')
        exc = cleaned_data.get('Exc')
        subj = cleaned_data.get("Subj")
        alpha = cleaned_data.get("alpha")
        if self.err == "dim":
            raise forms.ValidationError("The selected statistical map and mask do not have the same dimensions.")
        if self.err == "median":
            raise forms.ValidationError("Are you sure this is a statistical map?  The interquartile range is extremely large.")
        if url and not spmfile == None:
            raise forms.ValidationError("Please choose: either paste a link to the data or upload your map.  Not both.")
        if not url and spmfile == None:
            raise forms.ValidationError("Please tell us where to find the data: either paste a link to the data or upload your map.")
        if url and spmfile == None:
            if not (url.endswith('.nii.gz') or url.endswith('.nii.gz')):
                raise forms.ValidationError("The statistical map has the wrong format: please choose a nifti-file")
        if not url and not spmfile == None:
            if not (spmfile.name.endswith('.nii') or spmfile.name.endswith('.nii.gz')):
                raise forms.ValidationError("The statistical map has the wrong format: please choose a nifti-file")
            if spmfile.size > 10**7:
                raise forms.ValidationError("Maximum file size for the statistical map: 100 MB")
        if not maskfile == None:
            if not (maskfile.name.endswith('.nii') or maskfile.name.endswith('.nii.gz')):
                raise forms.ValidationError("The mask has the wrong format: please choose a nifti-file")
            if maskfile.size > 10**7:
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
            'Data location',
            HTML("""<h6 style="margin-left: 15px">Data location: Either paste a link to the online nifti-file <b>OR</b> upload your statistical map.</h6>"""),
            'url',
            #HTML("""<h4 style="margin-left: 15px">OR</h4>"""),
            'spmfile',
            ),
        Fieldset(
            'Mask location (optional)',
            HTML("""<h6 style="margin-left: 15px">Upload a full brain mask or a Region-of-Interest mask.  If no mask is selected, all non-null voxels are used.</h6>"""),
            'maskfile'
        ),
        Fieldset(
            'Design specifications',
            'ZorT','Exc','Subj','Samples','alpha'
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
        ButtonHolder(Submit('Submit', 'Submit parameters', css_class='btn-black')),
        HTML("""<br><br><br><br><br>"""),
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
