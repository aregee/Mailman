# Create your views here.
from restfm.models import *
from restfm.serializers import *
from rest_framework import generics 
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete, pre_save
from django.db import models
from django.dispatch import receiver
from django.http import Http404
from mailmanclient import Client, MailmanConnectionError
from social_auth.signals import socialauth_registered
from urllib2 import HTTPError

import os

import time

import subprocess

from mocker import Mocker

mocker = Mocker()

from mailmanclient import Client 


client = Client('%s/3.0' % settings.REST_SERVER, settings.API_USER, settings.API_PASS)

class ApiView(generics.ListCreateAPIView):

    serializer_class = MailmanSerializer

    def list(self, request, *args, **kwargs):
        dict = []
        for i in client.domains:
            dict.append(i.base_url)
        listObj = MailmanObject(field=dict)
        serializer = self.serializer_class(listObj)
        return Response(serializer.data)

class MyView(generics.ListCreateAPIView):

    serializer_class = MailmanSerializer

    def list(self, request, *args, **kwargs):
        listObj = MailmanObject(field=client.domains)
        serializer = self.serializer_class(listObj)
        return Response(serializer.data)
