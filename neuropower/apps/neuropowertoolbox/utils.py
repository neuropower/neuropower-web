from .models import NeuropowerModel
from .forms import ParameterForm, PeakTableForm, MixtureForm, PowerTableForm, PowerForm
import requests
import os
os.environ['http_proxy']=''
import urllib
from django.conf import settings
from django.http import HttpResponseRedirect

def get_neuropower_steps(template_page,sid,pi1=None):

    '''get_neuropower_steps returns a complete dictionary object with button colors, active status, and  currently active based on a template page and session data object.
    '''

    # template name, step class, and color
    pages = {"neuropower/neuropowerstart.html": {"class":"overview","color":"#F7F7F7","enabled":"yes"},
             "neuropower/neuropowerinput.html": {"class":"start","color":"#F7941E","enabled":"yes"},
             "neuropower/neuropowerviewer.html": {"class":"viewer","color":"#FFDE16","enabled":"yes"},
             "neuropower/neuropowertable.html": {"class":"peak-table","color":"#D7DF21","enabled":"yes"},
             "neuropower/neuropowermodel.html": {"class":"fit","color":"#0BA14B","enabled":"yes"},
             "neuropower/neuropowersamplesize.html": {"class":"power-calculation","color":"#25AAE1","enabled":"yes"},
             "neuropower/neuropowercrosstab.html": {"class":"power-table","color":"#25AAE1","enabled":"yes"}}

    # Set enabled or disabled page status depending on session data
    if not NeuropowerModel.objects.filter(SID=sid):
        pages["neuropower/neuropowerviewer.html"]["enabled"] = "no"
        pages["neuropower/neuropowertable.html"]["enabled"] = "no"
        pages["neuropower/neuropowermodel.html"]["enabled"] = "no"
        pages["neuropower/neuropowersamplesize.html"]["enabled"] = "no"
        pages["neuropower/neuropowercrosstab.html"]["enabled"] = "no"

    else:
        neuropowerdata = NeuropowerModel.objects.get(SID=sid)

        if neuropowerdata.step == 0:
            pages["neuropower/neuropowerviewer.html"]["enabled"] = "no"
            pages["neuropower/neuropowertable.html"]["enabled"] = "no"
            pages["neuropower/neuropowermodel.html"]["enabled"] = "no"
            pages["neuropower/neuropowersamplesize.html"]["enabled"] = "no"
            pages["neuropower/neuropowercrosstab.html"]["enabled"] = "no"

        if neuropowerdata.step == 1:
            pages["neuropower/neuropowersamplesize.html"]["enabled"] = "no"
            pages["neuropower/neuropowercrosstab.html"]["enabled"] = "no"

        if neuropowerdata.step == 2:
            pages["neuropower/neuropowercrosstab.html"]["enabled"] = "no"

        if pi1==0:
            pages["neuropower/neuropowersamplesize.html"]["enabled"] = "no"
            pages["neuropower/neuropowercrosstab.html"]["enabled"] = "no"

    # Set the active page
    pages["active"] = pages[template_page]
    return pages


def get_db_entries(template_page,sid):

    '''get_db_entries checks which db models have entries, and can as such redirect to right page if a certain model is missing.
    '''
    # template name, step class, and color
    relink = {"pm":"neuropower/neuropowerinput",
            "ptm":"neuropower/neuropowertable",
            "mm":"neuropower/neuropowermodel",
            "powerm":"neuropower/neuropowersamplesize"}
    message = {"pm":"Your session has expired and we can't find the description of the data.  Please fill out this form again to access your power analysis.",
            "ptm":"Something went wrong and we couldn't find the table of extracted peaks, so we've sent you back to this page.  Don't worry, we re-calculated the table here,so you can continue your power analysis now.",
            "mm":"Something went wrong and we couldn't find the estimated mixture distribution for your power analysis.  Don't worry, we re-estimated the model here, so you can continue your power analysis now.",
            "powerm":"Something went wrong and we couldn't find the power estimates for your power analysis.  Don't worry, we re-estimated the power curves here, so you can continue your power analysis now."
            }

    err = ""

    if template_page == "neuropower/neuropowerviewer.html":
        if not NeuropowerModel.objects.filter(SID=sid):
            err = "pm"

    elif template_page == "neuropower/neuropowertable.html":
        if not NeuropowerModel.objects.filter(SID=sid):
            err = "pm"

    elif template_page == "neuropower/neuropowermodel.html":
        if not NeuropowerModel.objects.filter(SID=sid):
            err = "pm"
        else:
            neuropowerdata = NeuropowerModel.objects.get(SID=sid)
            if neuropowerdata.step == 1:
                err = "ptm"

    elif template_page == "neuropower/neuropowersamplesize.html":
        if not NeuropowerModel.objects.filter(SID=sid):
            err = "pm"
        else:
            neuropowerdata = NeuropowerModel.objects.get(SID=sid)
            if neuropowerdata.step == 1:
                err = "ptm"
            elif neuropowerdata.step == 2:
                err = "mm"

    elif template_page == "neuropower/neuropowercrosstab.html":
        if not NeuropowerModel.objects.filter(SID=sid):
            err = "pm"
        else:
            neuropowerdata = NeuropowerModel.objects.get(SID=sid)
            if neuropowerdata.step == 1:
                err = "ptm"
            elif neuropowerdata.step == 2:
                err = "mm"
            elif neuropowerdata.step == 3:
                err = "powerm"

    if not err == "":
        link = "http://www.neuropowertools.org/"+relink[err]+"/?message="+message[err]
    else:
        link = ""

    return link

def get_url(url,return_json=True):
    '''get_url uses requests to return a url. Default return format is json. If return_json is set to false, will return raw data
    :param url: the url to retrieve
    :param return_json: boolean, default True, to return json
    '''
    response = requests.get(url)
    if return_json == True:
        return response.json()
    else:
        return response.text


def get_session_id(request):
    '''get_session_id gets the user session id, and creates one if it doesn't exist'''
    if not request.session.exists(request.session.session_key):
        request.session.create()
    sid = request.session.session_key
    return(sid)


def create_local_copy(map_url,map_local):
    if map_url.split(".")[-1] == "gz":
        map_local = map_local+".nii.gz"
    else:
        map_local = map_local+".nii"
    urllib.urlretrieve(map_url,map_local)
    # response = requests.get(map_url,stream=True)
    # if response.status_code == 200:
    #     with open(map_local,"wb") as f:
    #         f.write(response.raw.read())

    return map_local

def get_neurovault_form(request,neurovault_id):
    neurovault_image = get_url("http://neurovault.org/api/images/%s/?format=json" %(neurovault_id))
    collection_id = str(neurovault_image['collection_id'])

    message = None
    if not (neurovault_image['map_type'] == 'Z map' or neurovault_image['map_type'] == 'T map' or neurovault_image['analysis_level']==None):
        message = "Power analyses can only be performed on Z or T maps."
    if not (neurovault_image['analysis_level'] == 'group' or neurovault_image['analysis_level']==None):
        message = "Power analyses can only be performed on group statistical maps."

    parsform = ParameterForm(request.POST or None,
                             request.FILES or None,
                             default_url = "",
                             err = '',
                             initial = {"map_url":neurovault_image["file"],
                                        "ZorT":"T" if neurovault_image["map_type"] =="T map" else "Z",
                                        "Subj":neurovault_image["number_of_subjects"]})

    out = {
        "parsform": parsform,
        "message": message
    }

    return out
