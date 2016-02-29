import tempfile
import os
import urllib
from django.conf import settings

def create_temporary_copy(path,mapID):
    #temp_dir = tempfile.gettempdir()
    temp_dir = settings.MEDIA_ROOT
    temp_path = os.path.join(temp_dir,'maps','SPM_'+mapID+'.nii.gz')
    urllib.urlretrieve(path, temp_path)
    return temp_path
