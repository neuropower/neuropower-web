from models import DesignModel
from crispy_forms.layout import Submit, Layout, Field, Div, HTML, Fieldset, ButtonHolder
from crispy_forms.bootstrap import PrependedAppendedText, FormActions
from crispy_forms.helper import FormHelper
from django.core import exceptions
from django import forms

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
        fields = ['C00','C01','C02','C03','C04','C05','C06','C07','C08','C09',
        'C10','C11','C12','C13','C14','C15','C16','C17','C18','C19',
        'C20','C21','C22','C23','C24','C25','C26','C27','C28','C29',
        'C30','C31','C32','C33','C34','C35','C36','C37','C38','C39',
        'C40','C41','C42','C43','C44','C45','C46','C47','C48','C49',
        'P0','P1','P2','P3','P4','P5','P6','P7','P8','P9']

    def __init__(self,*args,**kwargs):
        super(DesignConsForm,self).__init__(*args,**kwargs)

    def clean(self):
        cleaned_data = super(DesignConsForm,self).clean()
        return cleaned_data

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.label_class = 'col-lg-12'
    helper.layout = Layout(
        Fieldset(
            'Probabilities',
            HTML("""<h5> What are the expected probabilities for each trialtype? </h5>"""),
            Div(
            Div(Field('P0'),css_class='col-xs-1'),
            Div(Field('P1'),css_class='col-xs-1'),
            Div(Field('P2'),css_class='col-xs-1'),
            Div(Field('P3'),css_class='col-xs-1'),
            Div(Field('P4'),css_class='col-xs-1'),
            Div(Field('P5'),css_class='col-xs-1'),
            Div(Field('P6'),css_class='col-xs-1'),
            Div(Field('P7'),css_class='col-xs-1'),
            Div(Field('P8'),css_class='col-xs-1'),
            Div(Field('P9'),css_class='col-xs-1'),
            css_class='row-md-12 col-xs-12'
            )
            ),
        Fieldset(
            'Contrasts',
            HTML("""<h5> What contrasts will be tested? </h5>"""),
            HTML("""<h6> Contrast 1 </h6>"""),
            Div(
            Div(Field('C00'),css_class='col-xs-1'),
            Div(Field('C01'),css_class='col-xs-1'),
            Div(Field('C02'),css_class='col-xs-1'),
            Div(Field('C03'),css_class='col-xs-1'),
            Div(Field('C04'),css_class='col-xs-1'),
            Div(Field('C05'),css_class='col-xs-1'),
            Div(Field('C06'),css_class='col-xs-1'),
            Div(Field('C07'),css_class='col-xs-1'),
            Div(Field('C08'),css_class='col-xs-1'),
            Div(Field('C09'),css_class='col-xs-1'),
            css_class='row-md-12 col-xs-12'
            ),
            HTML("""<h6> Contrast 2 </h><br><br>"""),
            Div(
            Div(Field('C10'),css_class='col-xs-1'),
            Div(Field('C11'),css_class='col-xs-1'),
            Div(Field('C12'),css_class='col-xs-1'),
            Div(Field('C13'),css_class='col-xs-1'),
            Div(Field('C14'),css_class='col-xs-1'),
            Div(Field('C15'),css_class='col-xs-1'),
            Div(Field('C16'),css_class='col-xs-1'),
            Div(Field('C17'),css_class='col-xs-1'),
            Div(Field('C18'),css_class='col-xs-1'),
            Div(Field('C19'),css_class='col-xs-1'),
            css_class='row-md-12 col-xs-12'
            ),
            HTML("""<h6> Contrast 3 </h><br><br>"""),
            Div(
            Div(Field('C20'),css_class='col-xs-1'),
            Div(Field('C21'),css_class='col-xs-1'),
            Div(Field('C22'),css_class='col-xs-1'),
            Div(Field('C23'),css_class='col-xs-1'),
            Div(Field('C24'),css_class='col-xs-1'),
            Div(Field('C25'),css_class='col-xs-1'),
            Div(Field('C26'),css_class='col-xs-1'),
            Div(Field('C27'),css_class='col-xs-1'),
            Div(Field('C28'),css_class='col-xs-1'),
            Div(Field('C29'),css_class='col-xs-1'),
            css_class='row-md-12 col-xs-12'
            ),
            HTML("""<h6> Contrast 4 </h><br><br>"""),
            Div(
            Div(Field('C30'),css_class='col-xs-1'),
            Div(Field('C31'),css_class='col-xs-1'),
            Div(Field('C32'),css_class='col-xs-1'),
            Div(Field('C33'),css_class='col-xs-1'),
            Div(Field('C34'),css_class='col-xs-1'),
            Div(Field('C35'),css_class='col-xs-1'),
            Div(Field('C36'),css_class='col-xs-1'),
            Div(Field('C37'),css_class='col-xs-1'),
            Div(Field('C38'),css_class='col-xs-1'),
            Div(Field('C39'),css_class='col-xs-1'),
            css_class='row-md-12 col-xs-12'
            ),
            HTML("""<h6> Contrast 5 </h><br><br>"""),
            Div(
            Div(Field('C40'),css_class='col-xs-1'),
            Div(Field('C41'),css_class='col-xs-1'),
            Div(Field('C42'),css_class='col-xs-1'),
            Div(Field('C43'),css_class='col-xs-1'),
            Div(Field('C44'),css_class='col-xs-1'),
            Div(Field('C45'),css_class='col-xs-1'),
            Div(Field('C46'),css_class='col-xs-1'),
            Div(Field('C47'),css_class='col-xs-1'),
            Div(Field('C48'),css_class='col-xs-1'),
            Div(Field('C49'),css_class='col-xs-1'),
            css_class='row-md-12 col-xs-12'
            ),
            HTML("""<br><br><br><br><br>"""),
            ButtonHolder(Submit('Submit', 'Submit parameters', css_class='btn-black')),
            HTML("""<br><br><br><br><br>""")
        )
    )
