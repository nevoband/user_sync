#!/usr/bin/env python

import requests
import pprint
from requests_ntlm import HttpNtlmAuth

class Sharepoint:

    def __init__(self,username,password,url, contextUrl, sharepointListName):
        self.username = username
        self.password = password
        self.url = url
        self.contextUrl = contextUrl
        self.sharepointListName = sharepointListName

        headers = {
            "Accept":"application/json; odata=verbose",
            "Content-Type":"application/json; odata=verbose",
            "odata":"verbose",
            "X-RequestForceAuthentication":"true"
        }
        
        auth = HttpNtlmAuth(self.username, self.password)
        
