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
        fields = ['ITI','TR','L','S','Clen']

    def __init__(self,*args,**kwargs):
        super(DesignMainForm,self).__init__(*args,**kwargs)
        self.fields['ITI'].label = "Inter-trial interval (s)?"
        self.fields['TR'].label = "Scanner TR (s)"
        self.fields['S'].label = "Trialtypes"
        self.fields['L'].label = "Total number of trials"
        self.fields['Clen'].label = 'Number of contrasts'

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
            ),
        HTML("""<br><br><br><br><br>"""),
        ButtonHolder(Submit('Submit', 'Next', css_class='btn-black')),
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
        self.stim = kwargs.pop('stim')
        self.cons = kwargs.pop('cons')
        super(DesignConsForm,self).__init__(*args,**kwargs)
        s = 0
        for field in self.fields.keys():
            s = s+1
            snew = "stim "+str(s) if s<10 else ""
            self.fields[field].label=snew

    def clean(self):
        cleaned_data = super(DesignConsForm,self).clean()
        return cleaned_data

    #stim=self.stim
    #cons=self.cons
    stim=3
    cons=2
    cssclass = "col-xs-"+str(int(np.floor(12/stim)))
    fields = [['C00','C01','C02','C03','C04','C05','C06','C07','C08','C09'],
        ['C10','C11','C12','C13','C14','C15','C16','C17','C18','C19'],
        ['C20','C21','C22','C23','C24','C25','C26','C27','C28','C29'],
        ['C30','C31','C32','C33','C34','C35','C36','C37','C38','C39'],
        ['C40','C41','C42','C43','C44','C45','C46','C47','C48','C49']]
    fieldsP = ['P0','P1','P2','P3','P4','P5','P6','P7','P8','P9']
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.label_class = 'col-lg-12'
    helper.layout = Layout()
    # probabilities
    helper.layout.append(HTML('<h5> What are the probabilities for each stimulus type? </h5>'))
    helper.layout.append(HTML('<br>'))
    for indf,field in enumerate(fieldsP):
        helper.layout.append(Div(Field(field,type='hidden' if indf>=stim else None),css_class=cssclass))
    helper.layout.append(HTML('<br><br><br><br><br>'))
    # contrasts
    helper.layout.append(HTML('<h5> What are the specific contrasts that will be tested? </h5>'))
    for indl,line in enumerate(fields):
        # titles
        if indl<=cons:
            if indl>0:
                helper.layout.append(HTML("<br><br><br><br>"))
            helper.layout.append(HTML('<h6> Contrast %s </h6>'%(indl+1)))
        # fields
        for indf,field in enumerate(fields[indl]):
            helper.layout.append(Div(Field(field,type='hidden' if indf>=stim or indl>cons else None),css_class=cssclass))
    helper.layout.append(HTML("<br><br><br><br>"))
    helper.layout.append(ButtonHolder(Submit('Submit', 'Submit parameters', css_class='btn-secondary')))
