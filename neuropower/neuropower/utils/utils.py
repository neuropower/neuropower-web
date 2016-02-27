import tempfile
import os
import urllib

def create_temporary_copy(path,sid):
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, 'nifti_down_"+sid+".nii.gz')
    urllib.urlretrieve(path, temp_path)
    return temp_path
