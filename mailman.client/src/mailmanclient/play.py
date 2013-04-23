#! /bin/python

import os,time,subprocess 
import json

from mailmanclient import Client , MailmanConnectionError 

client = Client('http://localhost:8001/3.0','restadmin', 'restpass')
var = client.domains



class MailmanRestManager(object):
    """Manager class to give a model class CRUD access to the API.
    Returns objects (or lists of objects) retrived from the API.
    """
    
    def __init__(self, resource_name, resource_name_plural, api_vers):
        self.client = Client('http://localhost:8001/3.0','restadmin', 'restpass')
        self.resource_name = resource_name
        self.resource_name_plural = resource_name_plural
        
        self.api_vers = json.dumps(client.system)


    
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

        
    
   

objects = MailmanRestManager('domain','domains','value')


print objects.resource_name
print objects.api_vers
print objects.all()
print objects.get()
print objects.byname("rahulgaur.info")
