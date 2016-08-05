from models import DesignModel
from crispy_forms.layout import Submit, Layout, Field, Div, HTML, Fieldset, ButtonHolder
from crispy_forms.bootstrap import PrependedAppendedText, FormActions
from crispy_forms.helper import FormHelper
from django.core import exceptions
from django import forms
import numpy as np

class DesignMainForm(forms.ModelForm):
    class Meta:
        model = DesignModel
        fields = ['ITI','TR','L','S','Clen','ConfoundOrder','MaxRepeat','W1','W2','W3','W4']

    def __init__(self,*args,**kwargs):
        super(DesignMainForm,self).__init__(*args,**kwargs)
        self.fields['ITI'].label = "Inter-trial interval (s)?"
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
            Div(Field('ITI'),css_class='col-md-4 col-sm-6 col-xs-12'),
            Div(Field('TR'),css_class='col-md-4 col-sm-6 col-xs-12'),
            Div(Field('S'),css_class='col-md-4 col-sm-6 col-xs-12'),
            Div(Field('L'),css_class='col-md-4 col-sm-6 col-xs-12'),
            Div(Field('Clen'),css_class='col-md-4 col-sm-6 col-xs-12'),
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
        'C40','C41','C42','C43','C44','C45','C46','C47','C48','C49'
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
            HTML('<h5> What are the probabilities for each stimulus type? </h5><br>')
            )

        for indf,field in enumerate(fieldsP):
            self.helper.layout.append(
                Div(Field(field,type='hidden' if indf>=self.stim else None),css_class=cssclass)
                )

        self.helper.layout.append(
            HTML('<br><br><br><br><br>')
            )

        # add layout: contrasts

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
        HTML("<p>Run Genetic Algorithm</p>"),
        ButtonHolder(Submit('Run', 'Run !', css_class='btn-black')),
        HTML("""<br><br><br><br><br>"""),
        )

class DesignProbsForm(forms.ModelForm):
    class Meta:
        model = DesignModel
        fields = ['ITI']

    def __init__(self,*args,**kwargs):
        super(DesignProbsForm,self).__init__(*args,**kwargs)

    def clean(self):
        cleaned_data = super(DesignProbsForm,self).clean()
        return cleaned_data
