from __future__ import unicode_literals
import sys
sys.path = sys.path[1:]
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.conf import settings
from scipy.stats import norm, t
import os
from utils import get_session_id, probs_and_cons, get_design_steps, weights_html
from forms import DesignMainForm,DesignConsForm,DesignReviewForm,DesignWeightsForm, DesignProbsForm, DesignOptionsForm, DesignRunForm
from models import DesignModel
from designcore import design
import numpy as np
import time

## MAIN PAGE TEMPLATE PAGES

def FAQ(request):
    return render(request,"design/FAQ.html",{})

def tutorial(request):
    return render(request,"design/tutorial.html",{})

def methods(request):
    return render(request,"design/methods.html",{})

def start(request):

    # Get the template/step status

    template = "design/start.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template,sid)

    return render(request,template,context)

def maininput(request):

    # Get the template/step status

    template = "design/input.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template,sid)

    try:
        desdata = DesignModel.objects.get(SID=sid)
    except DesignModel.DoesNotExist:
        desdata = None

    # Define form

    inputform = DesignMainForm(request.POST or None,instance=desdata)

    # If page was result of POST or not valid: show form with db entries
    # Else: go to next page

    if not request.method=="POST" or not inputform.is_valid():
        context["inputform"] = inputform
        return render(request,template,context)
    else:

        # initial save

        form = inputform.save(commit=False)
        form.SID = sid
        form.save()

        # get data and change parameters

        desdata = DesignModel.objects.get(SID=sid)
        weightsform = DesignWeightsForm(None, instance=desdata)
        weightsform = weightsform.save(commit=False)
        W = np.array([desdata.W1,desdata.W2,desdata.W3,desdata.W4])
        if np.sum(W)>1:
            W = W/np.sum(W)
        weightsform.W = W
        weightsform.save()

        return HttpResponseRedirect('../consinput/')

def consinput(request):

    # Get the template/step status

    template = "design/cons.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template,sid)

    try:
        desdata = DesignModel.objects.get(SID=sid)
    except DesignModel.DoesNotExist:
        desdata = None
        inputform = DesignMainForm(request.POST or None, instance=desdata)
        template = 'design/input.html'
        message = "Before you can fill out the contrasts and trial probabilities, you'll first need to fill out this form with basic information about your design."
        context = {
            "inputform": inputform,
            "message": message,
            "steps":get_design_steps(template,sid)
        }
        return render(request,template,context)

    # Define form

    consform = DesignConsForm(request.POST or None,instance=desdata,stim=desdata.S,cons=desdata.Clen)

    # If page was result of POST or not valid: show form with db entries
    # Else: go to next page

    if not request.method=="POST" or not consform.is_valid():
        context["consform"] = consform
        return render(request,template,context)
    else:
        form = consform.save(commit=False)
        form.SID = sid
        form.save()

        # get data and change parameters

        consform = DesignProbsForm(None, instance=desdata)
        consform = consform.save(commit=False)
        matrices = probs_and_cons(sid)
        consform.P = matrices['P']
        consform.C = matrices['C']
        consform.save()

        return HttpResponseRedirect('../review/')

def review(request):

    # Get the template/step status

    template = "design/review.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template,sid)

    try:
        desdata = DesignModel.objects.get(SID=sid)
    except DesignModel.DoesNotExist:
        desdata = None
        inputform = DesignMainForm(request.POST or None, instance=desdata)
        template = 'design/input.html'
        message = "Before you can review your settings, you'll first need to fill out this form with basic information about your design."
        context = {
            "inputform": inputform,
            "message": message,
            "steps":get_design_steps(template,sid)
        }
        return render(request,template,context)

    # Define form

    revform = DesignReviewForm(request.POST or None,instance=desdata)
    context["revform"] = revform

    # Set summary variables in context

    matrices = probs_and_cons(sid)
    context['ITI']=desdata.ITI
    context['TR']=desdata.TR
    context['S']=desdata.S
    context['L']=desdata.L
    context["Phtml"] = matrices["Phtml"]
    context["Chtml"] = matrices["Chtml"]
    context["Whtml"] = weights_html(desdata.W)
    context["order"] = desdata.ConfoundOrder
    context["repeat"] = desdata.MaxRepeat

    # If page was result of POST: show summary
    # Else: go to next page

    if not request.method=="POST":
        return render(request,template,context)
    else:
        form = revform.save(commit=False)
        form.SID = sid
        form.save()

        return HttpResponseRedirect('../runGA/')

def options(request):

    # Get the template/step status

    template = "design/options.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template,sid)

    try:
        desdata = DesignModel.objects.get(SID=sid)
    except DesignModel.DoesNotExist:
        desdata = None
        inputform = DesignMainForm(request.POST or None, instance=desdata)
        template = 'design/input.html'
        message = "Before you can change the internal settings, you'll first need to fill out this form with basic information about your design."
        context = {
            "inputform": inputform,
            "message": message,
            "steps":get_design_steps(template,sid)
        }
        return render(request,template,context)

    # Define form

    opsform = DesignOptionsForm(request.POST or None,instance=desdata)
    context["opsform"] = opsform

    # If page was result of POST: show summary
    # Else: go to next page

    if not request.method=="POST":
        return render(request,template,context)
    else:
        form = opsform.save(commit=False)
        form.SID = sid
        form.save()
        return HttpResponseRedirect('../review/')

def runGA(request):

    # Get the template/step status

    template = "design/runGA.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template,sid)

    try:
        desdata = DesignModel.objects.get(SID=sid)
    except DesignModel.DoesNotExist:
        desdata = None
        inputform = DesignMainForm(request.POST or None, instance=desdata)
        template = 'design/input.html'
        message = "Before you can change the internal settings, you'll first need to fill out this form with basic information about your design."
        context = {
            "inputform": inputform,
            "message": message,
            "steps":get_design_steps(template,sid)
        }
        return render(request,template,context)

    # Define form

    runform = DesignRunForm(request.POST or None,instance=desdata)
    context["runform"] = runform

    # Get parameters to GA

    matrices = probs_and_cons(sid)
    desfile = os.path.join(settings.MEDIA_ROOT,"designs",str(sid)+".json")
    if os.path.isfile(desfile):
        os.remove(desfile)

    des = design.GeneticAlgorithm(
        # design specific
        ITI = desdata.ITI,
        TR = desdata.TR,
        L = desdata.L,
        P = matrices["P"],
        C = matrices["C"],
        weights = desdata.W,
        ConfoundOrder = desdata.ConfoundOrder,
        MaxRepeat = desdata.MaxRepeat,
        # general/defaulted
        rho = desdata.rho,
        Aoptimality = True if desdata.Aoptimality==1 else False,
        saturation = True if desdata.Saturation==1 else False,
        resolution = desdata.resolution,
        G = desdata.G,
        q = desdata.q,
        I = desdata.I,
        cycles = desdata.cycles,
        preruncycles = desdata.preruncycles,
        write = desfile
    )

    # Example responsive loop
    if not request.method=="POST":
        return render(request,template,context)
    else:
        if request.POST.get("GA")=="Stop":
            # set 'stop' in db to 1
            form = runform.save(commit=False)
            form.stop = 1
            form.save()
            return HttpResponseRedirect('../runGA/')

        if request.POST.get("GA")=="Run":
            # set 'stop' in db to 0
            form = runform.save(commit=False)
            form.stop = 0
            form.save()

            # check whether loop is already running
            desdata = DesignModel.objects.get(SID=sid)

            if desdata.running==0:
                form.running = 1
                form.save()

                # Run !
                for loop in range(1000):
                    #check whether stop signal is given
                    desdata = DesignModel.objects.get(SID=sid)
                    if desdata.stop == 1:
                        break
                    time.sleep(1)
                    print(loop)

                form.running = 0
                form.save()
                print("stopped")


        # postval = request.POST.get("GA")
        # print(postval)
        # running = 0
        # if postval == "Run" and running == 0:
        #     for loop in range(1000):
        #         running = 1
        #         postval = request.POST.get("GA")
        #         print(postval)
        #         if postval == "Stop":
        #             break
        #         time.sleep(1)
        #
        # postval = request.POST.get("GA")
        # print(postval)
        # running = 0
        # if postval == "Run" and running == 0:
        #
        #     # Compute maximum efficiency
        #     postval = request.POST.get("GA")
        #     if des.weights[2]>0 or des.weights[3]>0 and postval=="Run":
        #         print("running maxef 1")
        #         nulorder = [np.argmin(des.P)]*des.L
        #         NulDesign = {"order":nulorder}
        #         NulDesign = des.CreateDesignMatrix(NulDesign)
        #         des.FfMax = des.FfCalc(NulDesign)['Ff']
        #         des.FcMax = des.FcCalc(NulDesign)['Fc']
        #
        #     # prerun for FeMax #
        #     postval = request.POST.get("GA")
        #     if des.weights[0]>0 and postval=="Run":
        #         print("running maxef FE")
        #         des.prerun = 'Fe'
        #         des.counter = 1
        #         Generation = {'order':[],'F':[],'ID':[]}
        #         des.GeneticAlgorithmCreateOrder()
        #         Generation = des.GeneticAlgorithmAddOrder(Generation,[7,7,6])
        #         Best = []
        #         for gen in range(des.preruncycles):
        #             postval = request.POST.get("GA")
        #             print(postval)
        #             if postval == "Stop":
        #                 break
        #             des.counter = des.counter + 1
        #             print("Generation: "+str(gen+1))
        #             NextGen = des.GeneticAlgorithmGeneration(Generation)
        #             Generation = NextGen["NextGen"]
        #             Best.append(NextGen['FBest'])
        #             des.FeMax = Best[-1]
        #
        #     # prerun for FdMax #
        #     postval = request.POST.get("GA")
        #     if des.weights[1]>0 and postval == "Run":
        #         print("running maxef FD")
        #         des.prerun = 'Fd'
        #         des.counter = 1
        #         Generation = {'order':[],'F':[],'ID':[]}
        #         des.GeneticAlgorithmCreateOrder()
        #         Generation = des.GeneticAlgorithmAddOrder(Generation,[7,7,6])
        #         Best = []
        #         for gen in range(des.preruncycles):
        #             postval = request.POST.get("GA")
        #             print(postval)
        #             if postval == "Stop":
        #                 break
        #             des.counter = des.counter + 1
        #             print("Generation: "+str(gen+1))
        #             NextGen = des.GeneticAlgorithmGeneration(Generation)
        #             Generation = NextGen["NextGen"]
        #             Best.append(NextGen['FBest'])
        #             des.FdMax = Best[-1]
        #
        #     postval = request.POST.get("GA")
        #     if not postval=="Stop":
        #         print("Initiating")
        #         # Initiate !
        #         self.counter = 1
        #         Generation = {'order':[],'F':[],'ID':[]}
        #         self.GeneticAlgorithmCreateOrder()
        #         Generation = self.GeneticAlgorithmAddOrder(Generation,[7,7,6])
        #
        #     postval = request.POST.get("GA")
        #     if not postval=="Stop":
        #         print("Running GA")
        #         for gen in range(desdata.cycles):
        #             postval = request.POST.get("GA")
        #             print(postval)
        #             if postval == "Stop":
        #                 break
        #                 return  HttpResponseRedirect('../consinput/')
        #             running = running+1
        #             self.counter = self.counter + 1
        #             print("Generation: "+str(gen+1))
        #             NextGen = des.GeneticAlgorithmGeneration(Generation)
        #             Generation = NextGen["NextGen"]
        #             Best.append(NextGen['FBest'])
        #             if self.write:
        #                 with open(self.write,'w') as fp:
        #                     json.dump(Generation,fp)
        #             running = 0
        #     print("Stopped or done !")
        #
        # else:
        #     return HttpResponseRedirect('../runGA/')
        #
        # des.GeneticAlgorithm()


    return render(request,template,context)

### SESSION CONTROL

def end_session(request):
    '''ends a session so the user can start a new one.'''
    try:
        request.session.flush()
    except KeyError:
        pass
    return neuropowerinput(request,end_session=True)
