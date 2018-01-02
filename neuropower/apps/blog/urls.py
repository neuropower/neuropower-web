from django.conf.urls import url
from django.contrib import admin
import django.views.defaults
from . import views


urlpatterns = [
    url(r'^blog/$',views.blog,name='blog')
    ]
