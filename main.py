from config import (KAYAKO_API_URL,
                    KAYAKO_API_KEY,
                    KAYAKO_SECRET_KEY,
                    HF_API_URL,
                    HF_API_KEY,
                    HF_AUTH_KEY)
from kayako import (KayakoAPI,
                    User,
                    Department,
                    Ticket)
import requests
import hashlib
import random
import base64
import hmac
import string
import xmltodict
import json
import datetime

"""#{{{
The handle kApi is for communicating with the
Kayako API respectively.
"""#}}}
kApi = KayakoAPI(KAYAKO_API_URL, KAYAKO_API_KEY, KAYAKO_SECRET_KEY)
hApi = (HF_API_KEY, HF_AUTH_KEY)

def getKayakoSignature():#{{{
    """
    This functions creates a random salt and hashes the salt
    with KAYAKO_SECRET_KEY. This is required only if directly
    calling the XML API of kayako instead of using the python
    API
    """
    salt = ''.join([random.choice(string.ascii_letters+string.digits) for _ in range(30)])
    signature = hmac.new(KAYAKO_SECRET_KEY, msg=salt, digestmod=hashlib.sha256).digest()
    encodedSignature = base64.b64encode(signature)
    return salt, encodedSignature#}}}

def postToHappyFox(endpoint, payload):#{{{
    """
    Makes post requests to the happyfox URL
    """
    url = HF_API_URL + endpoint
    headers = { "Content-Type": "application/json" }
    response = requests.post(url,
                data=payload,
                headers=headers,
                auth=(HF_API_KEY, HF_AUTH_KEY))
    return response#}}}

def getFromKayako(endpoint):#{{{
    """
    Makes get requests to the Kayako URL
    """
    salt, signature = getKayakoSignature()
    payload = dict(apikey=KAYAKO_API_KEY, e=endpoint, salt=salt, signature=signature)
    return requests.get(KAYAKO_API_URL, params=payload)#}}}


class Contacts(object):
    """#{{{
    The Contacts class is used for manipulating contacts on both
    Kayako and Happyfox. The kayako related methods start with
    'k' and the happyfox related methods start with 'h'.
    """#}}}

    #def _kXMLContactsToDict(self, responsetext):#{{{
        #u = xmltodict.parse(responsetext)['users']['user']
        #for i, u in enumerate(u):
            #self.kayako_users[i+1] = dict(u)#}}}

    #def kGetContactsInRange(self, fromindex=1, toindex=1000):#{{{
        #endpoint = '/Base/User/Filter/{0}/{1}'.format(fromindex, toindex)
        #response = getFromKayako(endpoint)
        #self._kXMLContactsToDict(response.text)
        #return self.kayako_users#}}}

    def _kGetAllContacts(self):
        endpoint = '/Base/User/Filter'
        response = getFromKayako(endpoint)
        u = xmltodict.parse(response.text)['users']['user']
        kayako_users = dict()
        for i, u in enumerate(u, 1):
            kayako_users[i] = dict(u)
        return kayako_users

    def hCreateAllContacts(self):
        kayako_users = self._kGetAllContacts()
        happyfox_contacts = dict()
        for k, v in kayako_users.items():
            happyfox_contacts[k] = dict(name=v['fullname'], email=v['email'])
        jsonpayload = json.dumps(happyfox_contacts.values())
        return postToHappyFox('users/', jsonpayload)

    def hGetContacts():
        pass

class Departments(object):
    def kGetAllDepartments(self):
       return kApi.get_all(Department)

class Tickets(object):

    def _kGetAllTickets(self):
        import pudb; pu.db
        import shelve
        s = shelve.open('../main.hg/tempdata')
        tkts = s['tkts']
        s.close()
        return tkts

        depts = Departments().kGetAllDepartments()
        kayako_tickets = list()
        for d in depts:
            kayako_tickets.extend(kApi.get_all(Ticket, d.id))
        return kayako_tickets

    def hCreateAllTickets(self):
        kayako_tickets = self._kGetAllTickets()
        hf_dict_tkts = list()
        for t in kayako_tickets:
            hf_tkt = dict(created_at=t.creationtime,
                            subject=t.subject,
                            text=t.subject,
                            category=1,
                            priority=1,
                            email=t.email,
                            name=t.fullname)
            hf_dict_tkts.append(hf_tkt)
        endpoint = 'tickets/'
        payload = json.dumps(hf_dict_tkts, cls=DateEncoder)
        return postToHappyFox(endpoint, payload)

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%dT%H:%M:%S")
        return json.JSONEncoder.default(self, obj)

def main():
    #createContacts

    #createTickets
    Tickets().hCreateAllTickets()


main()

