from __future__ import unicode_literals
from django.db import models

class NiftiModel(models.Model):
    file = models.URLField()
    def __unicode__(self): # Python 3: __str__
        return self.file
