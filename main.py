from config import (KAYAKO_API_URL,
                    KAYAKO_API_KEY,
                    KAYAKO_SECRET_KEY,
                    HF_API_URL,
                    HF_API_KEY,
                    HF_AUTH_KEY)
from kayako import (KayakoAPI,
                    User,
                    Department,
                    Ticket,
                    Staff)
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
def getFromHappyFox(endpoint):
    return requests.get(HF_API_URL + endpoint, auth=hApi)

def getFromKayako(endpoint):#{{{
    """
    Makes get requests to the Kayako URL
    """
    salt, signature = getKayakoSignature()
    payload = dict(apikey=KAYAKO_API_KEY, e=endpoint, salt=salt, signature=signature)
    return requests.get(KAYAKO_API_URL, params=payload)#}}}


class Contacts(object):#{{{
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
        return kayako_users.values(), postToHappyFox('users/', jsonpayload)

    def hGetContacts():
        pass#}}}

class Departments(object):
    def kGetAllDepartments(self):
        return kApi.get_all(Department)

    def hGetAllCategories(self):
        return getFromHappyFox("categories/")


class Tickets(object):
    def __init__(self, kayako_users):
        self.kayako_users = kayako_users

    def _kGetAllTickets(self):
        depts = Departments().kGetAllDepartments()
        kayako_tickets = list()
        kayako_departments = dict()
        for d in depts:
            kayako_tickets.extend(kApi.get_all(Ticket, d.id))
            kayako_departments[d.id] = d.title
        return kayako_departments, kayako_tickets

    def _kGetTicketUpdates(self, ticketid):
        return kApi.get_all(TicketPost, ticketid)

    def _kGetAllStaff(self):
        staff = kApi.get_all(Staff)
        kayako_staff = dict()
        for s in staff:
            kayako_staff[s.id] = s.firstname + ' ' + s.lastname
        return kayako_staff

    def _hGetAllStaff(self):
        happyfox_staff = dict()
        for s in getFromHappyFox('staff/').json():
            happyfox_staff[s['name']] = s['id']
        return happyfox_staff

    def _hGetAllContacts(self):
        happyfox_contacts = dict()
        pageinfo = getFromHappyFox('users/?size=50&page=1/').json()
        pagecount = pageinfo['page_info']['page_count']
        for c in pageinfo['data']:
            happyfox_contacts[c['name']] = c['id']

        if page_count > 1:
            for page in xrange(2, page_count+1)
                for c in getFromHappyFox('users/?size=50&page{0}'.format(page)).json()['data']
                    happyfox_contacts[c['name']] = c['id']
        return happyfox_contacts

    def _kGetAllUsers(self):
        kayako_users = dict()
        for ku in self.kayako_users:
            kayako_users[ku['id']] = ku['fullname']
        return kayako_users

    def hCreateAllTickets(self):
        #Tickets and departments/categories from kayako
        kayako_departments, kayako_tickets = self._kGetAllTickets()

        #Get all categories from hf and put in a dict
        happyfox_category = dict()
        for category in getFromHappyFox('categories/').json():
            happyfox_category[category['name']] = category['id']

        #Get happyfox and kayako staff
        happyfox_staff, kayako_staff = self._hGetAllStaff(), self._kGetAllStaff()

        #Get happyfox contacts and kayako users
        happyfox_contacts, kayako_users = _hGetAllContacts(), _kGetAllUsers()

        hf_dict_tkts = list()
        hf_dict_tkt_updates = list()
        for i, t in enumerate(kayako_tickets, 1):
            kayako_ticketupdates = self._kGetTicketUpdates(t.id)
            hf_tkt = dict(created_at=t.creationtime,
                            subject=t.subject,
                            text=kayako_ticketupdates[0].contents,
                            category=happyfox_category[kayako_departments[t.departmentid]],
                            priority=1,
                            email=t.email,
                            name=t.fullname)
            hf_tkt['t-cf-1'] = t.id
            hf_dict_tkts.append(hf_tkt)

            for ku in kayako_ticketupdates:
                hf_tkt_update = dict()
                if ku.staffid:
                    hf_tkt_update['staff'] = happyfox_staff[kayako_staff[ku.staffid]]
                    hf_tkt_update['text'] = ku.contents
                else:
                    hf_tkt_update['user'] = happyfox_contacts[kayako_users[str(ku.userid)]]
                    hf_tkt_update['text'] = ku.contents

            print "Completed imported ticket {0}".format(t.id)
            print "Completed {0}/{1}".format(i, len(kayako_tickets))

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
    kayako_users, response = Contacts().hCreateAllContacts()

    #createTickets
    Tickets(kayako_users).hCreateAllTickets()


main()
