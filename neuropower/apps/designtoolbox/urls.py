from . import views
from django.conf.urls import url
from django.contrib import admin
import django.views.defaults

urlpatterns = [
    url(r'^FAQ/$',views.FAQ,name='dFAQ'),
    url(r'^tutorial/$',views.tutorial,name='dTutorial'),
    url(r'^methods/$',views.methods,name='dMethods'),
    ]
