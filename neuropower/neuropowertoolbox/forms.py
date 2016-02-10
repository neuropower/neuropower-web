from django import forms
from django.forms import fields
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML
from crispy_forms.bootstrap import (
    PrependedText, PrependedAppendedText, FormActions)

class ParameterForm(forms.Form):
    ZorT_c = (
        (1,("T")),
        (2,("Z"))
    )
    ZorT = forms.ChoiceField(
        label="Are the values Z- or T-values?",
        required=True,
        choices=ZorT_c
        )
    ExcUnits_c = (
        (1,("units = p-values (SPM default)")),
        (2,("units = t-values (FSL default)"))
    )
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
    Smoothx = forms.CharField(
        label="",
        widget=forms.TextInput(attrs={'placeholder':'x'})
        )
    Smoothy = forms.CharField(
        label="",
        widget=forms.TextInput(attrs={'placeholder':'y'})
        )
    Smoothz = forms.CharField(
        label="",
        widget=forms.TextInput(attrs={'placeholder':'z'})
        )
    Voxx = forms.CharField(
        label="",
        widget=forms.TextInput(attrs={'placeholder':'x'})
        )
    Voxy = forms.CharField(
        label="",
        widget=forms.TextInput(attrs={'placeholder':'y'})
        )
    Voxz = forms.CharField(
        label="",
        widget=forms.TextInput(attrs={'placeholder':'z'})
        )

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.add_input(Submit('login', 'login', css_class='btn-primary'))
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
        )

    )



class SimpleForm(forms.Form):
    username = forms.CharField(label="Username", required=True)
    password = forms.CharField(
        label="Password", required=True, widget=forms.PasswordInput)
    remember = forms.BooleanField(label="Remember Me?")

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.add_input(Submit('login', 'login', css_class='btn-primary'))

class CartForm(forms.Form):
    item = forms.CharField()
    quantity = forms.IntegerField(label="Qty")
    price = forms.DecimalField()

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.layout = Layout(
        'item',
        PrependedText('quantity', '#'),
        PrependedAppendedText('price', '$', '.00'),
        FormActions(Submit('login', 'login', css_class='btn-primary'))
    )


class CreditCardForm(forms.Form):
    fullname = forms.CharField(label="Full Name", required=True)
    card_number = forms.CharField(label="Card", required=True, max_length=16)
    expire = forms.DateField(label="Expire Date", input_formats=['%m/%y'])
    ccv = forms.IntegerField(label="ccv")
    notes = forms.CharField(label="Order Notes", widget=forms.Textarea())

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.label_class = 'col-sm-2'
    helper.field_class = 'col-sm-4'
    helper.layout = Layout(
        Field('fullname', css_class='input-sm'),
        Field('card_number', css_class='input-sm'),
        Field('expire', css_class='input-sm'),
        Field('ccv', css_class='input-sm'),
        Field('notes', rows=3),
        FormActions(Submit('purchase', 'purchase', css_class='btn-primary'))
    )
