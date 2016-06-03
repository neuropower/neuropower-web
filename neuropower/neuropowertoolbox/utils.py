from neuropowertoolbox.models import ParameterModel, MixtureModel, PeakTableModel, PowerTableModel
import requests
import os
os.environ['http_proxy']=''
import urllib
from django.conf import settings
from django.http import HttpResponseRedirect

def get_neuropower_steps(template_page,session_id=None,pi1=None):
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
    if not ParameterModel.objects.filter(SID=session_id):
        pages["neuropower/neuropowerviewer.html"]["enabled"] = "no"
        pages["neuropower/neuropowertable.html"]["enabled"] = "no"
        pages["neuropower/neuropowermodel.html"]["enabled"] = "no"
        pages["neuropower/neuropowersamplesize.html"]["enabled"] = "no"
        pages["neuropower/neuropowercrosstab.html"]["enabled"] = "no"

    if not PeakTableModel.objects.filter(SID=session_id):
        pages["neuropower/neuropowermodel.html"]["enabled"] = "no"
        pages["neuropower/neuropowersamplesize.html"]["enabled"] = "no"
        pages["neuropower/neuropowercrosstab.html"]["enabled"] = "no"

    if not MixtureModel.objects.filter(SID=session_id):
        pages["neuropower/neuropowersamplesize.html"]["enabled"] = "no"
        pages["neuropower/neuropowercrosstab.html"]["enabled"] = "no"

    if not PowerTableModel.objects.filter(SID=session_id):
        pages["neuropower/neuropowercrosstab.html"]["enabled"] = "no"

    if pi1==0:
        pages["neuropower/neuropowersamplesize.html"]["enabled"] = "no"
        pages["neuropower/neuropowercrosstab.html"]["enabled"] = "no"

    # Set the active page
    pages["active"] = pages[template_page]
    return pages


def get_db_entries(template_page,session_id=None):
    '''get_db_entries checks which db models have entries, and can as such redirect to right page if a certain model is missing.
    '''
    # template name, step class, and color
    relink = {"pm":"neuropowerinput",
            "ptm":"neuropowertable",
            "mm":"neuropowermodel",
            "powerm":"neuropowersamplesize"}
    message = {"pm":"Your session has expired and we can't find the description of the data.  Please fill out this form again to access your power analysis.",
            "ptm":"Something went wrong and we couldn't find the table of extracted peaks, so we've sent you back to this page.  Don't worry, we re-calculated the table here,so you can continue your power analysis now.",
            "mm":"Something went wrong and we couldn't find the estimated mixture distribution for your power analysis.  Don't worry, we re-estimated the model here, so you can continue your power analysis now.",
            "powerm":"Something went wrong and we couldn't find the power estimates for your power analysis.  Don't worry, we re-estimated the power curves here, so you can continue your power analysis now."
            }

    err = ""

    if template_page == "neuropower/neuropowerviewer.html":
        if not ParameterModel.objects.filter(SID=session_id):
            err = "pm"

    elif template_page == "neuropower/neuropowertable.html":
        if not ParameterModel.objects.filter(SID=session_id):
            err = "pm"

    elif template_page == "neuropower/neuropowermodel.html":
        if not ParameterModel.objects.filter(SID=session_id):
            err = "pm"
        elif not PeakTableModel.objects.filter(SID=session_id):
            err = "ptm"

    elif template_page == "neuropower/neuropowersamplesize.html":
        if not ParameterModel.objects.filter(SID=session_id):
            err = "pm"
        elif not PeakTableModel.objects.filter(SID=session_id):
            err = "ptm"
        elif not MixtureModel.objects.filter(SID=session_id):
            err = "mm"

    elif template_page == "neuropower/neuropowercrosstab.html":
        if not ParameterModel.objects.filter(SID=session_id):
            err = "pm"
        elif not PeakTableModel.objects.filter(SID=session_id):
            err = "ptm"
        elif not MixtureModel.objects.filter(SID=session_id):
            err = "mm"
        elif not PowerTableModel.objects.filter(SID=session_id):
            err = "powerm"

    if not err == "":
        link = "http://192.168.99.100/"+relink[err]+"/?message="+message[err]
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


def create_temporary_copy(file,mapID,mask=False,url=False):
    temp_dir = os.path.join(settings.MEDIA_ROOT,"maps")
    end = file[-3:]
    newext = ".nii.gz" if end == ".gz" else ".nii"
    if not mask:
        newfilename = os.path.join(temp_dir,'SPM_'+mapID+newext)
    else:
        newfilename = os.path.join(temp_dir,"mask_"+mapID+newext)

    if url:
        newfilename = os.path.join(temp_dir,'SPM_'+mapID+newext)
        urllib.urlretrieve(file, newfilename)
    else:
        os.rename(file,newfilename)
    return newfilename
