from __future__ import unicode_literals
import sys
sys.path = sys.path[1:]
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, render_to_response
from django.core.mail import send_mail
from django.conf import settings
import os

def blog(request):
    context = {}
    context['thanks'] = True

    return render(request, "blog/blog.html", context)
