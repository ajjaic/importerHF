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
                    Staff,
                    TicketPost,
                    TicketAttachment)
import tempfile
import os
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

def postToHappyFox(endpoint, payload, files=None):#{{{
    """
    Makes post requests to the happyfox URL
    """
    url = HF_API_URL + endpoint
    if not files:
        response = requests.post(url,
                    data=payload,
                    #headers={ "Content-Type": "application/json" },
                    auth=(HF_API_KEY, HF_AUTH_KEY))
    else:
        response = requests.post(url,
                    data=payload,
                    #headers = { "Content-Type": "multipart/form-data" },
                    files=files,
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
        #jsonpayload = json.dumps(happyfox_contacts.values())
        #return kayako_users.values(), postToHappyFox('users/', jsonpayload)
        return kayako_users.values(), postToHappyFox('users/', happyfox_contacts.values())

    def hGetContacts():
        pass#}}}

class Departments(object):#{{{
    def kGetAllDepartments(self):
        return kApi.get_all(Department)

    def hGetAllCategories(self):
        return getFromHappyFox("categories/")#}}}


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

        if pagecount > 1:
            for page in xrange(2, page_count+1):
                for c in getFromHappyFox('users/?size=50&page{0}'.format(page)).json()['data']:
                    happyfox_contacts[c['name']] = c['id']
        return happyfox_contacts

    def _kGetAllUsers(self):
        kayako_users = dict()
        for ku in self.kayako_users:
            kayako_users[ku['id']] = ku['fullname']
        return kayako_users

    def hCreateAllTickets(self):
##        #Tickets and departments/categories from kayako
##        kayako_departments, kayako_tickets = self._kGetAllTickets()
##
##        #Get all categories from hf and put in a dict
##        happyfox_category = dict()
##        for category in getFromHappyFox('categories/').json():
##            happyfox_category[category['name']] = category['id']
##
##        #Get happyfox and kayako staff
##        happyfox_staff, kayako_staff = self._hGetAllStaff(), self._kGetAllStaff()
##
##        #Get happyfox contacts and kayako users
##        happyfox_contacts, kayako_users = self._hGetAllContacts(), self._kGetAllUsers()


        kayako_departments = getfromshelve('kayako_departments')
        kayako_tickets = getfromshelve('kayako_tickets')
        kayako_staff = getfromshelve('kayako_staff')
        kayako_users = getfromshelve('kayako_users')
        happyfox_staff = self._hGetAllStaff()
        happyfox_contacts = self._hGetAllContacts()
        happyfox_category = dict()
        for category in getFromHappyFox('categories/').json():
            happyfox_category[category['name']] = category['id']

        len_kayako_tickets = len(kayako_tickets)
        for i, t in enumerate(kayako_tickets, 1):
            kayako_ticketupdates = self._kGetTicketUpdates(t.id)
            hf_tkt = dict(created_at=t.creationtime.strftime("%Y-%m-%dT%H:%M:%S"),
                            subject=t.subject,
                            text=kayako_ticketupdates[0].contents,
                            category=happyfox_category[kayako_departments[t.departmentid]],
                            priority=1,
                            email=t.email,
                            name=t.fullname)
            hf_tkt['t-cf-1'] = t.id

            #Get this tickets attachments
            kayako_ticket_attachments = kApi.get_all(TicketAttachment, t.id)

            #Post attachment while ticket creation
            #TODO
            for attachment in kayako_ticket_attachments:
                first_update = kayako_ticketupdates[0]
                if first_update.id == attachment.ticketpostid:
                    m = kApi.get(TicketAttachment, t.id, attachment.id)

            happyfox_attachments = dict()
            hf_tkt_updates = list()
            for ku in kayako_ticketupdates[1:]:
                hf_tkt_update = dict()
                if ku.staffid:
                    hf_tkt_update['staff'] = happyfox_staff[kayako_staff[ku.staffid]]
                else:
                    hf_tkt_update['user'] = happyfox_contacts[kayako_users[str(ku.userid)]]

                hf_tkt_update['text'] = ku.contents
                hf_tkt_update['timestamp'] = ku.dateline.strftime("%Y-%m-%dT%H:%M:%S")
                hf_tkt_update['id'] = ku.id

                hf_tkt_updates.append(hf_tkt_update)


                for attachment in kayako_ticket_attachments:
                    if ku.id == attachment.ticketpostid:
                        m = kApi.get(TicketAttachment, t.id, attachment.id)
                        tempfile = create_temporary_file(m.filename, base64.b64decode(m.contents))
                        tupfile = ('attachments', (m.filename, open(tempfile, 'rb'), m.filetype))
                        if not happyfox_attachments.has_key(ku.id):
                            happyfox_attachments[ku.id] = [tupfile]
                        else:
                            happyfox_attachments[ku.id].append(tupfile)



            #Post the ticket first
            endpoint = 'tickets/'
            #payload = json.dumps([(hf_tkt)], cls=DateEncoder)
            #response = postToHappyFox(endpoint, payload)
            response = postToHappyFox(endpoint, hf_tkt)
            #ticketid = response.json()[0]['id']
            ticketid = response.json()['id']

            #Now post the tickets updates
            for u in hf_tkt_updates:
                if u.has_key('staff'):
                    endpoint = 'ticket/{0}/staff_update/'.format(ticketid)
                else:
                    endpoint = 'ticket/{0}/user_reply/'.format(ticketid)
                uid = u['id']
                del u['id']
                #payload = json.dumps(u, cls=DateEncoder)
                if happyfox_attachments.has_key(uid):
                    #response = postToHappyFox(endpoint, payload, files=happyfox_attachments[uid])
                    response = postToHappyFox(endpoint, u, files=happyfox_attachments[uid])
                else:
                    #postToHappyFox(endpoint, payload)
                    postToHappyFox(endpoint, u)

            #print "Completed imported ticket {0}".format(ticketid)
            print "Completed {0}/{1}".format(i, len_kayako_tickets)

#class DateEncoder(json.JSONEncoder):
    #def default(self, obj):
        #if isinstance(obj, datetime.datetime):
            #return obj.strftime("%Y-%m-%dT%H:%M:%S")
        #return json.JSONEncoder.default(self, obj)

def create_temporary_file(filename, contents):
    path = os.path.join(tempfile.gettempdir(), "KayakoImport", HF_API_KEY) + os.sep
    if not os.path.exists(path):
        os.makedirs(path)
    with open(path + filename, 'w') as f:
        f.write(contents)
    return path+filename

def main():
    #createContacts
    kayako_users, response = Contacts().hCreateAllContacts()

    #createTickets
    Tickets(kayako_users).hCreateAllTickets()

def nomain():
    kayako_users = getfromshelve('kayako_users')
    Tickets(kayako_users).hCreateAllTickets()

def getfromshelve(varname):
    import shelve
    s = shelve.open('../main.hg/tempdata')
    varvalue = s[varname]
    s.close()
    return varvalue

def putinshelve(varname, varvalue):
    import shelve
    s = shelve.open('../main.hg/tempdata')
    s[varname] = varvalue
    s.close()

nomain()
