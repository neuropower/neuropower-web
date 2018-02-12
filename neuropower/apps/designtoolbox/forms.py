from .models import DesignModel
from crispy_forms.layout import Submit, Layout, Field, Div, HTML, Fieldset
from crispy_forms.bootstrap import PrependedAppendedText, FormActions
from crispy_forms.helper import FormHelper
from django.core import exceptions
from django import forms
from neurodesign import generate
import numpy as np

class DesignMainForm(forms.ModelForm):
    class Meta:
        model = DesignModel
        fields = ['stim_duration','TR','L','S','Clen','Call','RestNum','RestDur','ConfoundOrder','MaxRepeat','W1','W2','W3','W4','duration_unitfree','duration_unit','durspec','ITImodel','ITIfixed','ITIunifmin','ITIunifmax','ITItruncmin','ITItruncmax','ITItruncmean','t_prestim','t_poststim']

    def __init__(self,*args,**kwargs):
        super(DesignMainForm,self).__init__(*args,**kwargs)
        self.fields['ITImodel'].label = "Choose a model to sample ITI's from"
        self.fields['ITIfixed'].label = "ITI duration (seconds)"
        self.fields['ITIunifmin'].label = "Minimum ITI (seconds)"
        self.fields['ITIunifmax'].label = "Maximum ITI (seconds)"
        self.fields['ITItruncmin'].label = "Minimum ITI (seconds)"
        self.fields['ITItruncmax'].label = "Maximum ITI (seconds)"
        self.fields['ITItruncmean'].label = "Average ITI (seconds)"
        self.fields['TR'].label = "Scanner TR (seconds)"
        self.fields['S'].label = "Number of stimulus types"
        self.fields['stim_duration'].label = "Stimulus duration (seconds)"
        self.fields['t_prestim'].label="Seconds before stimulus"
        self.fields['t_poststim'].label="Seconds after stimulus"
        self.fields['L'].label = "Total number of trials"
        self.fields['duration_unitfree'].label = 'Total duration of the task'
        self.fields['duration_unit'].label = 'Unit of duration'
        self.fields['Call'].label = 'Check to include all pairwise contrasts'
        self.fields['Clen'].label = 'Number of custom contrasts'
        self.fields['RestNum'].label = 'How many trials between rest blocks'
        self.fields['RestDur'].label = 'Duration of rest (seconds)'
        self.fields['ConfoundOrder'].label = 'Order of confounding control'
        self.fields['MaxRepeat'].label = 'Max number of repeated stimulus types'
        self.fields['W1'].label = 'Design efficiency'
        self.fields['W2'].label = 'Detection power'
        self.fields['W3'].label = 'Trial probabilities'
        self.fields['W4'].label = 'Psychological confounds'
        self.fields['durspec'].label = ""
        # self.fields['nested'].label = "Check for a nested design"
        # self.fields['nest_classes'].label = "If the design is nested, how many classes of stimulus types are there?"

    def clean(self):
        cleaned_data = super(DesignMainForm,self).clean()

        # if cleaned_data.get("ITI")<0:
        #     raise forms.ValidationError("ITI cannot be smaller than 0. Parameters not saved.")
        if cleaned_data.get("duspec") == 1 and cleaned_data.get("duration_unitfree")==None:
            raise forms.ValidationError("You need to specify the total duration of the experiment.")

        if cleaned_data.get("duspec") == 2 and cleaned_data.get("L")==None:
            raise forms.ValidationError("You need to specify the total number of trials.")

        if cleaned_data.get("TR")<0 or cleaned_data.get("TR")>10:
            raise forms.ValidationError("Are you sure about that TR? Parameters not saved.")

        if cleaned_data.get("S")>10:
            raise forms.ValidationError("Sorry, at the moment we can only model designs when there are at most 10 stimulus types. Parameters not saved.")

        if cleaned_data.get("S")==1:
            raise forms.ValidationError("Sorry, at the moment we can only model designs with more than 1 stimulus type.  Check back, this extension is on the agenda!")

        if cleaned_data.get("Clen")>5:
            raise forms.ValidationError("Sorry, at the moment we can only model designs when there are at most 5 contrasts. Parameters not saved.")

        if cleaned_data.get("Clen")==0 and cleaned_data.get("Call")==False:
            raise forms.ValidationError("Either choose a number of contrasts to be tested or choose all pairwise contrasts.")

        if cleaned_data.get("ConfoundOrder")>10:
            raise forms.ValidationError("Sorry, at the moment we can only model designs with a confoundorder smaller than 10. Parameters not saved.")

        if cleaned_data.get("ITImodel") == 1 and cleaned_data.get("ITIfixed")==None:
                raise forms.ValidationError("For a fixed ITI, please fill out the duration of the ITI's.")

        if cleaned_data.get("ITImodel") == 2 and (cleaned_data.get("ITItruncmin")==None or cleaned_data.get("ITItruncmax")==None or cleaned_data.get("ITItruncmean")==None):
                raise forms.ValidationError("For a truncated ITI, please fill out mean, min and max.")

        if cleaned_data.get("ITImodel") == 2:
            mn = cleaned_data.get("ITItruncmax")-cleaned_data.get("ITItruncmin")
            if mn < cleaned_data.get("ITItruncmean"):
                raise forms.ValidationError("You specified a truncated exponential for the ITI's, but the mean is larger than the mean between min and max.  This is not possible for a truncated exponential.")

        if cleaned_data.get("ITImodel") == 3 and (cleaned_data.get("ITIunifmin")==None or cleaned_data.get("ITIunifmax")==None):
                raise forms.ValidationError("For ITI's sampled from a uniform distribution, please fill out the min and max.")

        if cleaned_data.get("MaxRepeat") < 4:
                raise forms.ValidationError("It will be hard to avoid designs with a stimulus type repeated maximum 4 times.  In that case you might better manually design the experiment, rather than using an optimiser.")
                
        if cleaned_data.get("MaxRepeat") < 8 and (cleaned_data.get("S")<3 or clenaed_data.get("L")>100 or cleaned_data.get("duration")>600):
                raise forms.ValidationError("It will be hard to avoid designs with a stimulus type repeated maximum 8 given that you're looking for a longer design or one with fewer stimulus types.  In that case you might better manually design the experiment, rather than using an optimiser.")

        if cleaned_data.get("ITImean") > 50:
                raise forms.ValidationError("Are you sure about that ITI?  That looks too long.  Don't forget it's in seconds.")

        # if cleaned_data.get("ITImin")==None and cleaned_data.get("ITImax")==None and cleaned_data.get("ITImean")==None:
        #     raise forms.ValidationError("You need to specify at least either a range of ITI, or the average (fixed) ITI.")
        #
        # if (cleaned_data.get("ITImin")==None and not cleaned_data.get("ITImax")==None) or (cleaned_data.get("ITImax")==None and not cleaned_data.get("ITImin")==None):
        #     raise forms.ValidationError("You specified either a minimum or a maximum ITI.  You need to fill out both.")
        #
        if (cleaned_data.get("RestNum")>0 and cleaned_data.get("RestDur")==0):
            raise forms.ValidationError("You wanted restblocks but you didn't specify their duration.")

        smaller = [
            cleaned_data.get("TR")<0,
            cleaned_data.get("ITIunifmin")<0,
            cleaned_data.get("ITIfixed")<0,
            cleaned_data.get("ITIunifmax")<0,
            cleaned_data.get("ITItruncmax")<0,
            cleaned_data.get("ITItruncmin")<0,
            cleaned_data.get("ITItruncmean")<0,
            cleaned_data.get("S")<0,
            cleaned_data.get("stim_duration")<0,
            cleaned_data.get("L")<0,
            cleaned_data.get("Clen")<0,
            cleaned_data.get("RestNum")<0,
            cleaned_data.get("RestDur")<0,
            cleaned_data.get("ConfoundOrder")<0,
            cleaned_data.get("MaxRepeat")<0,
            cleaned_data.get("W1")<0,
            cleaned_data.get("W2")<0,
            cleaned_data.get("W3")<0,
            cleaned_data.get("W4")<0,
            cleaned_data.get("t_prestim")<0,
            cleaned_data.get("t_poststim")<0
        ]
        snone = [
            cleaned_data.get("TR")==None,
            cleaned_data.get("ITIunifmin")==None,
            cleaned_data.get("ITIfixed")==None,
            cleaned_data.get("ITIunifmax")==None,
            cleaned_data.get("ITItruncmax")==None,
            cleaned_data.get("ITItruncmin")==None,
            cleaned_data.get("ITItruncmean")==None,
            cleaned_data.get("S")==None,
            cleaned_data.get("stim_duration")==None,
            cleaned_data.get("L")==None,
            cleaned_data.get("Clen")==None,
            cleaned_data.get("RestNum")==None,
            cleaned_data.get("RestDur")==None,
            cleaned_data.get("ConfoundOrder")==None,
            cleaned_data.get("MaxRepeat")==None,
            cleaned_data.get("W1")==None,
            cleaned_data.get("W2")==None,
            cleaned_data.get("W3")==None,
            cleaned_data.get("W4")==None,
            cleaned_data.get("t_prestim")==None,
            cleaned_data.get("t_poststim")==None
        ]
        svalid = [True if a and not b else False for a,b in zip(smaller,snone)]
        if any(svalid):
            raise forms.ValidationError("Some values are smaller than zero.  Please check for errors or typo's.")

        return cleaned_data

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.label_class = 'col-lg-12'
    helper.layout = Layout(
        Fieldset(
            'Design parameters',
            HTML("""<h5 style="margin-left: 15px">These parameters refer to your design and need your careful attention.</h5><br>"""),
            Div(
            Div(Field('S'),css_class='col-md-6 col-sm-6 col-xs-12'),
            Div(Field('TR'),css_class='col-md-6 col-sm-6 col-xs-12'),
            css_class='row-md-12 col-xs-12'
            ),
            ),
        HTML("<br><br><br>"),
        Fieldset("",
            Div(
            HTML("""<h5 style="margin-left: 15px">Trial structure</h5><p style="margin-left: 20px"> What does one trial look like?  Probably there is some time before the stimulus of interest (the target), where a fixation cross is shown.  Maybe there is some time after the stimulus is presented.</p>"""),
            Div(Field('t_prestim'),css_class='col-md-4 col-sm-4 col-xs-12'),
            Div(Field('stim_duration'),css_class='col-md-4 col-sm-4 col-xs-12'),
            Div(Field('t_poststim'),css_class='col-md-4 col-sm-4 col-xs-12'),
        )),
        HTML("<br><br><br>"),
        Fieldset("",
            Div(
            HTML("""<h5 style="margin-left: 15px">Duration of experiment</h5><p style="margin-left: 20px"> <ul><li><b>If you give duration</b>: number of trials = duration/(trialduration + mean ITI)</li><li><b>If you give number of trials</b>: duration = (trialduration + mean ITI)* number of trials</li></ul><br>"""),
            Div(Field('durspec'),css_class='col-md-12 col-sm-12 col-xs-12',css_id="durspec")),
        ),
        HTML("<br>"),
        Fieldset(
            '',
            Div(
            Div(Field('duration_unitfree'),css_class='col-md-6 col-sm-6 col-xs-12'),
            Div(Field('duration_unit'),css_class='col-md-6 col-sm-6 col-xs-12'),
            css_class='row-md-12 col-xs-12',
            css_id = "duration"
            ),
            Div(
            Div(Field('L'),css_class='col-md-12 col-sm-12 col-xs-12'),
            css_class='row-md-12 col-xs-12',
            css_id = "trialcount"
            ),
            ),
        HTML("<br><br><br>"),
        Fieldset("",
            Div(
            HTML("""<br><h5 style="margin-left: 15px">Inter Trial Interval (ITI)</h5><p style="margin-left: 20px">The ITI's can be fixed or variable.   Variable ITI's can be sampled from a uniform model or a truncated exponential model.</p> <br>"""),
            Div(Field('ITImodel'),css_class='col-md-12 col-sm-12 col-xs-12',css_id="ITImodel")),
        ),
        HTML("<br>"),
        Fieldset(
            '',
            Div(
            Div(Field('ITIunifmin'),css_class='col-md-6 col-sm-6 col-xs-12'),
            Div(Field('ITIunifmax'),css_class='col-md-6 col-sm-6 col-xs-12'),
            css_class='row-md-12 col-xs-12',
            css_id = "uniform"
            ),
            Div(
            Div(Field('ITItruncmin'),css_class='col-md-4 col-sm-12 col-xs-12'),
            Div(Field('ITItruncmax'),css_class='col-md-4 col-sm-12 col-xs-12'),
            Div(Field('ITItruncmean'),css_class='col-md-4 col-sm-12 col-xs-12'),
            css_class='row-md-12 col-xs-12',
            css_id = "exp"
            ),
            Div(
            Div(Field('ITIfixed'),css_class='col-md-12 col-sm-12 col-xs-12'),
            css_class='row-md-12 col-xs-12',
            css_id = "fixed"
            ),
            ),
        HTML("<br><br>"),
        Fieldset(
            '',
            HTML("""<h5 style="margin-left: 15px">Contrasts</h5>
            <p style="margin-left: 20px">How many contrasts do you want to optimise?  You can choose to include all pairwise comparisons.  You can also add custom contrasts (to be specified on the next page).  You can do both.</p>"""),
            Div(
            Div(Field('Call'),css_class='col-lg-3 col-sm-12'),
            css_class='row-lg-12'
            ),
            Div(
            Div(Field('Clen'),css_class='col-lg-12'),
            css_class='row-md-12 col-xs-12'
            ),
            ),
        HTML("<br><br>"),
        Fieldset(
            '',
            HTML("""<h5 style="margin-left: 15px">Rest blocks</h5>
            <p style="margin-left: 20px">Do you want to include rest blocks? If not: leave these boxes empty.</p><br> """),
            Div(
            Div(Field('RestNum'),css_class='col-md-4 col-sm-6 col-xs-12'),
            Div(Field('RestDur'),css_class='col-md-4 col-sm-6 col-xs-12'),
            css_class='row-md-12 col-xs-12'
            )
            ),
        HTML("<br><br><br><br>"),
        # Fieldset(
        #     '',
        #     HTML("""<h5 style="margin-left: 15px">Nested designs: Is there a specific structure amongst the stimulus types?</h5>
        #     <p style="margin-left: 20px"><b>Example:</b> A researcher designs a task with two condition (congruent and incongruent).  Within those conditions, the subject is presented with either a go signal or a stop signal (no go).  As such the condition <b>go/no go</b> is nested within the condition <b>congruency</b>.</p>
        #     <p style="margin-left: 20px"><b>How to specify your structure?</b> Please provide the total number of stimulus types above at the lowest level.  For the stop signal example above, you have a total of 4 stimuli (congruent stop, congruent go, incongruent stop, incongruent go).  On the next page, you will be asked to group those stimuli in classes.</p>
        #     <!-- <p style="margin-left: 20px"><b>Why is this important?</b> In the design optimisation, you want to avoid psychological confounds: if congruent always follows congruent, the experiment is predictable and this can influence your results.  If you don't specify the nested structure, the algorithm will avoid the predictability of all stimuli, but not of the stimulus classes.  For example: the algorithm will avoid that a 'congruent stop' follows 'congruent go' as much as it follows 'incongruent stop'.  However, the algorithm will not avoid that 'congruent' follows 'congruent' more than 'incongruent'.  By specifying the nesting structure, the algorithm will avoid psychological confounding on all levels of the nested design.</p>
        #     <p style = 'margin-left: 20px'><b>Symmetry.</b>  We call a symmetric design if all conditions nested within amother condition are the same.  In the example above: both the congruent and the incongruent trials are presented with a go or a no go trial.  Failing to ticking this box for a symmetric design would lead to the fact that the psychological confounding is preserved for the upper level (congruent vs. noncongruent), but not for the lower level (go vs. no go).</p> -->
        #     """),
        #     Div(
        #     Div(Field('nested'),css_class='col-lg-3 col-sm-12'),
        #     css_class='row-md-12 col-xs-12'
        #     ),
        #     # Div(
        #     # Div(Field('nest_symmetry'),css_class='col-lg-3 col-sm-12'),
        #     # css_class='row-md-12 col-xs-12'
        #     # ),
        #     Div(
        #     Div(Field('nest_classes'),css_class='col-lg-12'),
        #     css_class='row-md-12 col-xs-12'
        #     ),
        #     ),
        # HTML("<br><br>"),
        Fieldset(
            'Design optimisation parameters',
            HTML("""<p>There are 4 criteria that quantify the optimality of the design:</p>
            <ol>
            <li> Estimation efficiency (estimating the HRF)
                <img src="../../static/img/info.png" data-toggle="tooltip" data-placement="right" title="A possible goal of the research is to estimate the exact shape of the signal (the HRF) after a stimulus has been presented.  This can be interesting for research into how the HRF varies accross subjects/regions/...  This outcome is also desirable when estimating connectivity between region/time series.  The optimisation algorithm will improve the likeliness to have a good estimate of the brain response at following a stimulus with a good temporal resolution." style="width:10px;"/>
            </li>
            <li> Detection power (activation detection)
                <img src="../../static/img/info.png" data-toggle="tooltip" data-placement="right" title="A potential goal of an fMRI study is to detect brain activation related to a certain task.  The keyword is contrast.  For example: the researcher wants to find which part of the brain is responsible for the contrast between seeing faces and houses, the contrast between angry and happy faces, or the contrast between auditory stimulation and nothing (baseline).  In this case, the optimisation algorithm will improve the statistical separation between the modeled conditions." style="width:10px;"/>
            </li>
            <li> Final frequencies of each trial type
                <img src="../../static/img/info.png" data-toggle="tooltip" data-placement="right" title="Sometimes, you can get higher detection power or estimation efficiency when the frequencies of the stimuli are slightly changed.  For example: in a stop-signal experiment, you want 30% of the stimuli to be stop-trials and 70% to be go-trials.  However, the genetic algorithm has a better detection power when the frequencies are changed from 30-70 to 25-75%.  In certain tasks (like a  basic stop-signal task), changing these frequencies can have a large psychological impact and you want to avoid changing the frequencies." style="width:10px;"/>
            </li>
            <li> Avoiding psychological confounds
                <img src="../../static/img/info.png" data-toggle="tooltip" data-placement="right" title="When a subject in the scanner can predict which stimulus will follow, the effect of that stimulus might be biased.  As such, it is important to avoid certain contingencies." style="width:10px;"/>
            </li>
            </ol>
            <p>Please provide the weights that you want to give to each of the design criteria.</p>
            <p> Ideally, the weights sum to 1.  If not, they will be rescaled as such. <br><br>"""),
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
            HTML('''<p>To prevent predictability of the design, you can control the number of times a stimulus type is repeated. </p>
            '''),
            Div(
            Div(Field('MaxRepeat'),css_class='col-xs-12'),
            css_class='row-md-12 col-xs-12'
            ),
        HTML("""<br><br><br><br><br>"""),
        FormActions(Submit('Submit', 'Save and next', css_class='btn-black')),
        HTML("""<br><br><br><br><br>""")
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
        'C40','C41','C42','C43','C44','C45','C46','C47','C48','C49','G','I'
        ]
        # fields.append('HardProb')

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
        if self.stim<6:
            cssclass = "col-xs-"+str(int(np.floor(12/self.stim)))
        else:
            cssclass = "col-xs-"+str(int(np.floor(12*2/(self.stim))))

        fields = [['C00','C01','C02','C03','C04','C05','C06','C07','C08','C09'],
            ['C10','C11','C12','C13','C14','C15','C16','C17','C18','C19'],
            ['C20','C21','C22','C23','C24','C25','C26','C27','C28','C29'],
            ['C30','C31','C32','C33','C34','C35','C36','C37','C38','C39'],
            ['C40','C41','C42','C43','C44','C45','C46','C47','C48','C49']]
        fieldsP = ['P0','P1','P2','P3','P4','P5','P6','P7','P8','P9']

        # add layout: probabilities

        self.helper.layout.append(
            Div(
            Field('G',type='hidden'),
            Field('I',type='hidden'),
            css_class=cssclass)
            )

        self.helper.layout.append(
            HTML('<h5> What are the probabilities (or relative frequencies) for each stimulus type? </h5><br>')
            )

        for indf,field in enumerate(fieldsP):
            self.helper.layout.append(
                Div(Field(field,type='hidden' if indf>=self.stim else None),css_class=cssclass)
                )

        self.helper.layout.append(
            HTML('<br><br><br><br><br>')
            )


        # add layout: contrasts

        if self.cons>0:
            self.helper.layout.append(
                HTML('<br><br><br><br><br>')
                )
            self.helper.layout.append(
                HTML('''<h5> What are the specific contrasts that will be tested? </h5><br>
                <p>If the contrast sums to 0, you will model the difference between stimuli.  Examples with 3 stimulus types:</p>
                <ul>
                <li>The contrast [1 0 -1] will model the difference between stimulus type 1 and stimulus type 3.</li>
                <li>The contrast [1 -0.5 -0.5] will model the difference between stimulus type 1 and the average of stimulus type 2 and 3.</li>
                </ul>
                <p>If the contrast sums to 1, you will model the main effect of a certain stimulus.  Examples with 3 stimulus types:</p>
                <ul>
                <li>The contrast [1 0 0] will model the main effect of stimulus type 1 (vs. baseline). </li>
                <li>The contrast [0.33,0.33,0.33] will model the average effect of all stimulus types versus baseline.  (don't worry that they don't exactly sum to 1, this will be rescaled)</li>
                </ul><br><br><br>
                ''')
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

        # finalise layout: submit FormActions

        self.helper.layout.append(
            HTML("<br><br><br><br>")
            )
        self.helper.layout.append(
            FormActions(Submit('Submit', 'Save and next', css_class='btn-secondary'))
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
        FormActions(Submit('Save', 'Save and next', css_class='btn-black')),
        HTML("""<br><br><br><br><br>"""),
        )

class DesignOptionsForm(forms.ModelForm):
    class Meta:
        model = DesignModel
        fields = ['rho','Aoptimality','resolution','G','q','I','cycles','preruncycles','conv_crit','HardProb','outdes','Optimisation']

    def __init__(self,*args,**kwargs):
        super(DesignOptionsForm,self).__init__(*args,**kwargs)
        self.fields['rho'].label = "The assumed temporal autocorrelation coefficient."
        self.fields['Aoptimality'].label = "Do you want to optimise using A-optimality or D-optimality?"
        #self.fields['Saturation'].label = "We assume that there is saturation in the BOLD-signal: the signal cannot exceed 2 times the height of the HRF.  This avoids that for an ITI going towards 0, the signal goes to infinity."
        self.fields['resolution'].label = "The resolution of the timing of stimuli."
        self.fields['G'].label = "How many designs go from one generation to the next?"
        self.fields['q'].label = "What percentage of the trials gets mutated?"
        self.fields['I'].label = "How many immigrants per generation?"
        self.fields['cycles'].label = "Number of generations (iterations or cycles)."
        self.fields['preruncycles'].label = "Number of generations in the prerun to define the maximum efficiency and detection power."
        self.fields['conv_crit'].label = "Number of stable generations to reach convergence"
        self.fields['HardProb'].label = "Do you want a hard limit on the probabilities? (experimental)"
        self.fields['outdes'].label = 'How many designs do you want to get?'
        self.fields['Optimisation'].label = "Do you want to optimise using the Genetic Algorithm or with random designs?"

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
            Div(Field('Optimisation'),css_class='col-xs-12'),
            Div(Field('resolution'),css_class='col-xs-12'),
            Div(Field('outdes'),css_class='col-xs-12'),
            Div(Field('HardProb'),css_class='col-xs-4'),
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
            Div(Field('conv_crit'),css_class='col-xs-12'),
            css_class='row-md-12 col-xs-12'
            )
            ),
        HTML("""<br><br><br><br><br>"""),
        FormActions(Submit('Submit', 'Save', css_class='btn-black')),
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
    helper.add_input(Submit('GA','Run',css_class=".btn-stanford"))
    helper.add_input(Submit('GA','Stop',css_class=".btn-stanford"))


class DesignRetrieveForm(forms.ModelForm):
    class Meta:
        model = DesignModel
        fields = "__all__"

    def __init__(self,*args,**kwargs):
        super(DesignRetrieveForm,self).__init__(*args,**kwargs)

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
        FormActions(Submit('Download', 'Download optimal sequence', css_class='btn-stanford')),
        )

class DesignCodeForm(forms.ModelForm):
    class Meta:
        model = DesignModel
        fields = []

    def __init__(self,*args,**kwargs):
        super(DesignCodeForm,self).__init__(*args,**kwargs)

    def clean(self):
        cleaned_data = super(DesignCodeForm,self).clean()
        return cleaned_data

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.label_class = 'col-lg-12'
    helper.layout = Layout(
        FormActions(Submit('Code', 'Download script', css_class='btn-stanford')),
        )

class ContactForm(forms.Form):
    contact_name = forms.CharField(required=True)
    contact_email = forms.EmailField(required=True)
    content = forms.CharField(
        required=True,
        widget=forms.Textarea
    )

    def __init__(self,*args,**kwargs):
        super(ContactForm,self).__init__(*args,**kwargs)

    def clean(self):
        cleaned_data = super(ContactForm,self).clean()
        return cleaned_data

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.label_class = 'col-lg-12'
    helper.layout = Layout(
        'contact_name',
        'contact_email',
        'content',
        FormActions(Submit('Submit', 'Send feedback', css_class='btn-black'))
    )


class DesignMailForm(forms.ModelForm):
    class Meta:
        model = DesignModel
        fields = ['name','email']

    def __init__(self,*args,**kwargs):
        super(DesignMailForm,self).__init__(*args,**kwargs)
        self.fields['name'].label = "Name"
        self.fields['name'].required = True
        self.fields['email'].label = "E-mail address"
        self.fields['email'].required=True

    def clean(self):
        cleaned_data = super(DesignMailForm,self).clean()

        if cleaned_data.get("mail")=="" or cleaned_data.get("email")=="":
            raise forms.ValidationError("Please fill out your name and email address.")

        return cleaned_data

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.label_class = 'col-lg-12'
    helper.layout = Layout(
        Fieldset(
            '',
            Div(
                Div(Field('name'),css_class='col-xs-12'),
                Div(Field('email'),css_class='col-xs-12')
                )
                ),
            HTML("""<br>"""),
            FormActions(Submit('Mail', 'Submit', css_class='btn-black')),
            HTML("""<br>""")
        )
