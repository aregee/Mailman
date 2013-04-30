# -*- coding: utf-8 -*-
# Copyright (C) 1998-2012 by the Free Software Foundation, Inc.
#
# This file is part of Postorius.
#
# Postorius is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# Postorius is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Postorius.  If not, see <http://www.gnu.org/licenses/>.

import os,time,subprocess 
import json
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete, pre_save
from tastypie import fields, utils
from django.dispatch import receiver
from django.http import Http404
from mailmanclient import Client, MailmanConnectionError
from tastypie.resources import Resource

post = Client('%s/3.0' % settings.REST_SERVER,
                             settings.API_USER, settings.API_PASS)

class MailmanRestManager(object):
    """Manager class to give a model class CRUD access to the API.
    Returns objects (or lists of objects) retrived from the API.
    """
    
    def __init__(self, resource_name, resource_name_plural, api_vers):
        self.client = Client('%s/3.0' % settings.REST_SERVER,
                             settings.API_USER, settings.API_PASS)
        self.resource_name = resource_name
        self.resource_name_plural = resource_name_plural
        
        self.api_vers =Client('http://localhost:8001/3.0','restadmin', 'restpass').system


    
    def all(self):
        try:
            return getattr(self.client, self.resource_name_plural)
        except AttributeError:
            raise MailmanApiError
        except MailmanConnectionError, e:
            raise MailmanApiError(e)

    def get(self, **kwargs):
        try:
            method = getattr(self.client, 'get_' + self.resource_name)
            return method(**kwargs)
        except AttributeError, e:
            raise MailmanApiError(e)
        except HTTPError, e:
            if e.code == 404:
                raise Mailman404Error
            else:
                raise
        except MailmanConnectionError, e:
            raise MailmanApiError(e)
        
    def byname(self, example):
        self.example = client.get_domain("aregee.com")

        
    
class MailResource(Resource):
    version = fields.CharField(attribute="version")
    domnm = fields.CharField(attribute="domnm")

    class Meta:
        resource_name = "post"
        object_class = MailmanRestManager
        
        
    def _client(self):
        return post.Client('%s/3.0' % settings.REST_SERVER,
                             settings.API_USER, settings.API_PASS)
    
    def _bucket(self):
        client = self._client()
        return client.bucket('domnm')
    

    def detail_uri_kwargs(self, bundle_or_obj):
    
        kwargs = {}

        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.uuid
        else:
            kwargs['pk'] = bundle_or_obj.uuid

        return kwargs

    def get_object_list(self, request):
        query = self._client().add('domnm')
        query.map("function(v) { var data = JSON.parse(v.values[0].data);return [[v.key, data]];}")
        results = []
        
        for result in query.run():
            new_obj = MailmanRestManager(initial=result[1])
            new_obj.version = result[0]
            results.append(new_obj)
        return results
    
    def obj_get_list(self, request=None, **kwargs):
        # Filtering disabled for brevity...
        return self.get_object_list(request)

    def obj_get(self, request=None, **kwargs):
        bucket = self._bucket()
        message = bucket.get(kwargs['pk'])
        return MailmanRestManager(initial=domnm.get_data())
    
