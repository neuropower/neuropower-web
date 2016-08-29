from .models import DesignModel
from crispy_forms.layout import Submit, Layout, Field, Div, HTML, Fieldset, ButtonHolder
from crispy_forms.bootstrap import PrependedAppendedText, FormActions
from crispy_forms.helper import FormHelper
from django.core import exceptions
from django import forms
import numpy as np

class DesignMainForm(forms.ModelForm):
    class Meta:
        model = DesignModel
        fields = ['ITImin','ITImax','TR','L','S','Clen','ConfoundOrder','MaxRepeat','W1','W2','W3','W4','mainpars']

    def __init__(self,*args,**kwargs):
        super(DesignMainForm,self).__init__(*args,**kwargs)
        self.fields['ITImin'].label = "Minimum ITI"
        self.fields['ITImax'].label = "Maximum ITI"
        self.fields['TR'].label = "Scanner TR (s)"
        self.fields['S'].label = "Stimulus types"
        self.fields['L'].label = "Total number of trials"
        self.fields['Clen'].label = 'Number of contrasts'
        self.fields['ConfoundOrder'].label = 'Order of confounding control'
        self.fields['MaxRepeat'].label = 'Max number of repeated stimulus types'
        self.fields['W1'].label = 'Design efficiency'
        self.fields['W2'].label = 'Detection power'
        self.fields['W3'].label = 'Psychological confounds'
        self.fields['W4'].label = 'Trial probabilities'

    def clean(self):
        cleaned_data = super(DesignMainForm,self).clean()

        # if cleaned_data.get("ITI")<0:
        #     raise forms.ValidationError("ITI cannot be smaller than 0. Parameters not saved.")

        if cleaned_data.get("TR")<0 or cleaned_data.get("TR")>5:
            raise forms.ValidationError("Are you sure about that TR? Parameters not saved.")

        if cleaned_data.get("S")>10:
            raise forms.ValidationError("Sorry, at the moment we can only model designs when there are at most 10 stimulus types. Parameters not saved.")

        if cleaned_data.get("Clen")>5:
            raise forms.ValidationError("Sorry, at the moment we can only model designs when there are at most 5 contrasts. Parameters not saved.")

        if cleaned_data.get("ConfoundOrder")>10:
            raise forms.ValidationError("Sorry, at the moment we can only model designs with a confoundorder smaller than 10. Parameters not saved.")

        return cleaned_data

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.label_class = 'col-lg-12'
    helper.layout = Layout(
        Fieldset(
            'Design parameters',
            HTML("""<h5 style="margin-left: 15px">These parameters refer to your design and need your careful attention.</h><br><br>"""),
            Div(
            Div(Field('TR'),css_class='col-md-4 col-sm-6 col-xs-12'),
            Div(Field('S'),css_class='col-md-4 col-sm-6 col-xs-12'),
            Div(Field('L'),css_class='col-md-4 col-sm-6 col-xs-12'),
            Div(Field('Clen'),css_class='col-md-4 col-sm-6 col-xs-12'),
            css_class='row-md-12 col-xs-12'
            ),
            HTML("""<br><br>""")
            ),
        Fieldset(
            '',
            HTML("""<h5 style="margin-left: 15px">In what range is the ITI?</h><br><br><p>For a fixed ITI, fill out two times the same ITI.</p>"""),
            Div(
            Div(Field('ITImin'),css_class='col-md-4 col-sm-6 col-xs-12'),
            Div(Field('ITImax'),css_class='col-md-4 col-sm-6 col-xs-12'),
            css_class='row-md-12 col-xs-12'
            )
            ),
        HTML("<br><br><br>"),
        Fieldset(
            'Design optimisation parameters',
            HTML("""<p>There are 4 criteria that quantify the optimality of the design:</p>
            <ol>
            <li> Estimation efficiency (estimating the HRF)</li>
            <li> Detection power (activation detection)</li>
            <li> Avoiding psychological confounds</li>
            <li> Final probabilities of each trial type</li>
            </ol>
            <p>Please provide the weights that you want to give to each of the design criteria.</p><br><br>"""),
            Div(
            Div(Field('W1'),css_class='col-md-3 col-sm-6 col-xs-12'),
            Div(Field('W2'),css_class='col-md-3 col-sm-6 col-xs-12'),
            Div(Field('W3'),css_class='col-md-3 col-sm-6 col-xs-12'),
            Div(Field('W4'),css_class='col-md-3 col-sm-6 col-xs-12'),
            css_class='row-md-12 col-xs-12'
            )
            ),
        HTML("<br><br><br>"),
        Fieldset(
            'Design specifications to avoid psychological confounding',
            HTML("""<h5 style="margin-left: 15px">Trial contingencies</h><br><br>"""),
            HTML('''<p>To prevent predictability of the design, you can control the contingencies in the design. Eg. </p>
            <ul>
            <li> Order 1: <b>P(AA) = P(BA)</b>.</li>
            <li> Order 2: <b>P(AxA) = P(BxA)</b></li>
            <li> Order 3: <b>P(AxxA) = P(BxxA)</b></li>
            <li> ... </li>
            </ul>
            <p> To which order do you wish to control the contingencies (maximum 10)? In other words: how far back do you want to control the predictability?  </p>
            '''),
            Div(
            Div(Field('ConfoundOrder'),css_class='col-xs-12'),
            css_class='row-md-12 col-xs-12'
            ),
            HTML("""<br><br><br><br><h5 style="margin-left: 15px">Trial blockedness</h><br><br>"""),
            HTML('''<p>To prevent predictability of the design, you can control the number of times a stimulus type is repeated.</p>
            '''),
            Div(
            Div(Field('MaxRepeat'),css_class='col-xs-12'),
            css_class='row-md-12 col-xs-12'
            ),
        HTML("""<br><br><br><br><br>"""),
        ButtonHolder(Submit('Submit', 'Save', css_class='btn-black')),
        HTML("""<br><br><br><br><br>"""),
        Div(Field('mainpars',type='hidden'),css_class='col-xs-12')
        )
    )


class DesignConsForm(forms.ModelForm):
    class Meta:
        model = DesignModel
        fields = ['P0','P1','P2','P3','P4','P5','P6','P7','P8','P9',
        'C00','C01','C02','C03','C04','C05','C06','C07','C08','C09',
        'C10','C11','C12','C13','C14','C15','C16','C17','C18','C19',
        'C20','C21','C22','C23','C24','C25','C26','C27','C28','C29',
        'C30','C31','C32','C33','C34','C35','C36','C37','C38','C39',
        'C40','C41','C42','C43','C44','C45','C46','C47','C48','C49','HardProb','G','conpars'
        ]

    def __init__(self,*args,**kwargs):

        # extract arguments for shape of form

        self.stim = kwargs.pop('stim')
        self.cons = kwargs.pop('cons')

        # add helper for layout of form

        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.field_class = 'col-lg-12'
        self.helper.label_class = 'col-lg-12'
        self.helper.layout = Layout(Fieldset("Contrasts and probabilities"))

        # define iterable fields and compute width of each box

        cssclass = "col-xs-"+str(int(np.floor(12/self.stim)))
        fields = [['C00','C01','C02','C03','C04','C05','C06','C07','C08','C09'],
            ['C10','C11','C12','C13','C14','C15','C16','C17','C18','C19'],
            ['C20','C21','C22','C23','C24','C25','C26','C27','C28','C29'],
            ['C30','C31','C32','C33','C34','C35','C36','C37','C38','C39'],
            ['C40','C41','C42','C43','C44','C45','C46','C47','C48','C49']]
        fieldsP = ['P0','P1','P2','P3','P4','P5','P6','P7','P8','P9']

        # add layout: probabilities

        self.helper.layout.append(
            Div(Field('G',type='hidden'),css_class=cssclass)
            )

        self.helper.layout.append(
            Div(Field("conpars",type='hidden'),css_class=cssclass)
            )

        self.helper.layout.append(
            HTML('<h5> What are the probabilities (or frequencies) for each stimulus type? </h5><br>')
            )

        for indf,field in enumerate(fieldsP):
            self.helper.layout.append(
                Div(Field(field,type='hidden' if indf>=self.stim else None),css_class=cssclass)
                )

        self.helper.layout.append(
            HTML('<br><br><br><br><br>')
            )

        # hard limit
        self.helper.layout.append(
            HTML('<h5> Do you want a hard limit on those probabilities? </h5><br><p>Check if you want to preserve the probabilities exactly.  This largely restricts the possibilities to search over, so you might want to change the number of cycles in the settings.</p>')
            )

        self.helper.layout.append(
            Div(Field("HardProb"),css_class='col-xs-1'),
            )

        # add layout: contrasts

        self.helper.layout.append(
            HTML('<br><br><br><br><br>')
            )
        self.helper.layout.append(
            HTML('<h5> What are the specific contrasts that will be tested? </h5><br>')
            )

        for indl,line in enumerate(fields): # loop over lines (contrasts)

            # titles
            if indl<self.cons:
                if indl>0:
                    self.helper.layout.append(HTML("<br><br><br><br>"))
                self.helper.layout.append(
                    HTML('<h6> Contrast %s </h6>'%(indl+1))
                    )

            # fields
            for indf,field in enumerate(fields[indl]): # loop over fields (stimuli)
                self.helper.layout.append(
                    Div(
                        Field(field,type='hidden' if indf>=self.stim or indl>=self.cons else None),
                        css_class=cssclass
                        )
                    )

        # finalise layout: submit ButtonHolder

        self.helper.layout.append(
            HTML("<br><br><br><br>")
            )
        self.helper.layout.append(
            ButtonHolder(Submit('Submit', 'Save', css_class='btn-secondary'))
            )

        # initiate the form

        super(DesignConsForm,self).__init__(*args,**kwargs)

        # only labels for the fields from the probabilities

        s = 0
        for field in self.fields.keys():
            s = s+1
            snew = "stim "+str(s) if s<10 else ""
            self.fields[field].label=snew

    def clean(self):
        cleaned_data = super(DesignConsForm,self).clean()
        return cleaned_data

class DesignReviewForm(forms.ModelForm):
    class Meta:
        model = DesignModel
        fields = []

    def __init__(self,*args,**kwargs):
        super(DesignReviewForm,self).__init__(*args,**kwargs)

    def clean(self):
        cleaned_data = super(DesignReviewForm,self).clean()
        return cleaned_data

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.label_class = 'col-lg-12'
    helper.layout = Layout(
        HTML("""<br><br><br><br><br>"""),
        ButtonHolder(Submit('Save', 'Save', css_class='btn-black')),
        HTML("""<br><br><br><br><br>"""),
        )

class DesignWeightsForm(forms.ModelForm):
    class Meta:
        model = DesignModel
        fields = '__all__'

    def __init__(self,*args,**kwargs):
        super(DesignWeightsForm,self).__init__(*args,**kwargs)

    def clean(self):
        cleaned_data = super(DesignWeightsForm,self).clean()
        return cleaned_data

class DesignProbsForm(forms.ModelForm):
    class Meta:
        model = DesignModel
        fields = '__all__'

    def __init__(self,*args,**kwargs):
        super(DesignProbsForm,self).__init__(*args,**kwargs)

    def clean(self):
        cleaned_data = super(DesignProbsForm,self).clean()
        return cleaned_data

class DesignOptionsForm(forms.ModelForm):
    class Meta:
        model = DesignModel
        fields = ['rho','Aoptimality','Saturation','resolution','G','q','I','cycles','preruncycles']

    def __init__(self,*args,**kwargs):
        super(DesignOptionsForm,self).__init__(*args,**kwargs)
        self.fields['rho'].label = "The assumed temporal autocorrelation coefficient."
        self.fields['Aoptimality'].label = "Do you want to optimise using A-optimality or D-optimality?"
        self.fields['Saturation'].label = "We assume that there is saturation in the BOLD-signal: the signal cannot exceed 2 times the height of the HRF.  This avoids that for an ITI going towards 0, the signal goes to infinity."
        self.fields['resolution'].label = "The resolution of the timing of stimuli."
        self.fields['G'].label = "How many designs go from one generation to the next?"
        self.fields['q'].label = "What percentage of the trials gets mutated?"
        self.fields['I'].label = "How many immigrants per generation?"
        self.fields['cycles'].label = "Number of generations (iterations or cycles)."
        self.fields['preruncycles'].label = "Number of generations in the prerun to define the maximum efficiency and detection power."

    def clean(self):
        cleaned_data = super(DesignOptionsForm,self).clean()
        return cleaned_data

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.label_class = 'col-lg-12'
    helper.layout = Layout(
        Fieldset(
            'Design and optimisation parameters',
            HTML("""<p>These parameters are hidden and the default values can be found below.  To change the parameters, fill out the fields you wish to change and click save.</p><br><br>"""),
            Div(
            Div(Field('rho'),css_class='col-xs-12'),
            Div(Field('Aoptimality'),css_class='col-xs-12'),
            Div(Field('Saturation'),css_class='col-xs-12'),
            Div(Field('resolution'),css_class='col-xs-12'),
            css_class='row-md-12 col-xs-12'
            )
            ),
        HTML("<br><br><br>"),
        Fieldset(
            'Genetic algorithm parameters',
            HTML("""<p>The following parameters are set for a good flow of the genetic algorithm.</p><br><br>"""),
            Div(
            Div(Field('G'),css_class='col-xs-12'),
            Div(Field('q'),css_class='col-xs-12'),
            Div(Field('I'),css_class='col-xs-12'),
            Div(Field('cycles'),css_class='col-xs-12'),
            Div(Field('preruncycles'),css_class='col-xs-12'),
            css_class='row-md-12 col-xs-12'
            )
            ),
        HTML("""<br><br><br><br><br>"""),
        ButtonHolder(Submit('Submit', 'Save', css_class='btn-black')),
        HTML("""<br><br><br><br><br>""")
    )

class DesignRunForm(forms.ModelForm):
    class Meta:
        model = DesignModel
        fields = []

    def __init__(self,*args,**kwargs):
        super(DesignRunForm,self).__init__(*args,**kwargs)

    def clean(self):
        cleaned_data = super(DesignRunForm,self).clean()
        return cleaned_data

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.label_class = 'col-lg-12'
    helper.layout = Layout(
        ButtonHolder(Submit('GA', 'Run', css_class='btn-black')),
        HTML("""&emsp;"""),
        ButtonHolder(Submit('GA', 'Stop', css_class='btn-black'))
        )

class DesignDownloadForm(forms.ModelForm):
    class Meta:
        model = DesignModel
        fields = []

    def __init__(self,*args,**kwargs):
        super(DesignDownloadForm,self).__init__(*args,**kwargs)

    def clean(self):
        cleaned_data = super(DesignDownloadForm,self).clean()
        return cleaned_data

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.label_class = 'col-lg-12'
    helper.layout = Layout(
        ButtonHolder(Submit('Download', 'Download optimal sequence', css_class='btn-black')),
        )
