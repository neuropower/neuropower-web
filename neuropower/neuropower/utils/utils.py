#import tempfile
import os
import urllib
from django.conf import settings

def create_temporary_copy(file,mapID,mask=False,url=False):
    #temp_dir = tempfile.gettempdir()
    temp_dir = os.path.join(settings.MEDIA_ROOT,"maps")
    end = file[-3:]
    newext = ".nii.gz" if end == ".gz" else ".nii"
    if not mask:
        newfilename = os.path.join(temp_dir,'SPM_'+mapID+newext)
    else:
        newfilename = os.path.join(temp_dir,"mask_"+mapID+newext)

    if url:
        urllib.urlretrieve(file, newfilename)
    else:
        os.rename(file,newfilename)
    return newfilename
