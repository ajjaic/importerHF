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

"""
The handles kApi and hApi are for communicating with the
Kayako and Happyfox APIs respectively.
"""
kApi = KayakoAPI(KAYAKO_API_URL, KAYAKO_API_KEY, KAYAKO_SECRET_KEY)
hApi = dict(auth=(HF_API_KEY, HF_AUTH_KEY))

def getKayakoSignature():
    """
    This functions creates a random salt and hashes the salt
    with KAYAKO_SECRET_KEY. This is required only if directly
    calling the XML API of kayako instead of using the python
    API
    """
    salt = ''.join([random.choice(string.ascii_letters+string.digits) for _ in range(30)])
    signature = hmac.new(KAYAKO_SECRET_KEY, msg=salt, digestmod=hashlib.sha256).digest()
    encodedSignature = base64.b64encode(signature)
    return salt, encodedSignature

def postToHappyFox(endpoint, payload):
    url = HF_API_URL + endpoint
    headers = { "Content-Type": "application/json" }
    response = requests.post(url,
                data=payload,
                headers=headers,
                auth=(HF_API_KEY, HF_AUTH_KEY))
    return response

def getFromKayako(endpoint):
    salt, signature = getKayakoSignature()
    payload = dict(apikey=KAYAKO_API_KEY, e=endpoint, salt=salt, signature=signature)
    return requests.get(KAYAKO_API_URL, params=payload)


class Contact(object):
    """
    The Contact class is used for manipulating contacts on both
    Kayako and Happyfox. The kayako related methods start with
    'k' and the happyfox related methods start with 'h'.
    """
    def __init__(self):
        self.kayako_users = dict()
        self.happyfox_contacts = dict()

    def kXMLContactsToDict(self, responsetext):
        u = xmltodict.parse(responsetext)['users']['user']
        for i, u in enumerate(u):
            self.kayako_users[i+1] = dict(u)

    def prepareHFContacts(self):
        for k, v in self.kayako_users.items():
            self.happyfox_contacts[k] = dict(name=v['fullname'], email=v['email'])

    def kGetContactsInRange(self, fromindex=1, toindex=1000):
        endpoint = '/Base/User/Filter/{0}/{1}'.format(fromindex, toindex)
        response = getFromKayako(endpoint)
        self.kXMLContactsToDict(response.text)
        return self.kayako_users

    def kGetAllContacts(self):
        endpoint = '/Base/User/Filter'
        response = getFromKayako(endpoint)
        self.kXMLContactsToDict(response.text)
        return self.kayako_users

    def hCreateBulkContacts(self):
        jsonpayload = json.dumps(self.happyfox_contacts.values())
        return postToHappyFox('users/', jsonpayload)

    def hGetContacts():
        pass

def main():
    c = Contact()
    #c.kGetAllContacts()
    import shelve
    s = shelve.open('../main.hg/tempdata')
    c.kayako_users = s['kayako_users']
    s.close()
    c.prepareHFContacts()
    r = c.hCreateBulkContacts()
    print r.text

main()
