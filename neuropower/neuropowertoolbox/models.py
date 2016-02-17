from __future__ import unicode_literals
from django.db import models

class NiftiModel(models.Model):
    url = models.URLField()
    location = models.CharField(max_length=300,default="/Users/Joke/Documents/Onderzoek/neuropower/neuropower-dev/neuropower/static_in_pro/our_static/img/zstat1.nii.gz")
    def __unicode__(self): # Python 3: __str__
        return self
