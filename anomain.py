from config import (KAYAKO_API_URL,#{{{
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
                    TicketAttachment,
                    TicketNote)
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
import datetime#}}}

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
    """
    The Contacts class is used for manipulating contacts on both
    Kayako and Happyfox. The kayako related methods start with
    'k' and the happyfox related methods start with 'h'.
    """

    #def _kGetAllUsers(self):
        #endpoint = '/Base/User/Filter'
        #response = getFromKayako(endpoint)
        #u = xmltodict.parse(response.text)['users']['user']
        #kayako_users = dict()
        #for i, u in enumerate(u, 1):
            #kayako_users[i] = dict(u)
        #return kayako_users

    #def hCreateAllContacts(self):
        #kayako_users = self._kGetAllUsers()
        #happyfox_contacts = dict()
        #for k, v in kayako_users.items():
            #happyfox_contacts[k] = dict(name=v['fullname'], email=v['email'])
        ##jsonpayload = json.dumps(happyfox_contacts.values())
        ##return kayako_users.values(), postToHappyFox('users/', jsonpayload)
        #return kayako_users.values(), postToHappyFox('users/', happyfox_contacts.values())

    #def hGetContacts():
        #pass#}}}

#class Departments(object):#{{{
    #def kGetAllDepartments(self):
        #return kApi.get_all(Department)

    #def hGetAllCategories(self):
        #return getFromHappyFox("categories/")#}}}


class Tickets(object):
    def __init__(self, hf_contacts,
                        hf_categories,
                        hf_staff,
                        k_users,
                        k_staff,
                        k_tickets,
                        k_departments):

        self.hf_contacts = hf_contacts
        self.hf_categories = hf_categories
        self.hf_staff = hf_staff

        self.k_users = k_users
        self.k_staff = k_staff
        self.k_tickets = k_tickets
        self.k_departments = k_departments

    #def _kGetAllTicketsAndDepartments(self):#{{{
        #depts = Departments().kGetAllDepartments()
        #kayako_tickets = list()
        #kayako_departments = dict()
        #for d in depts:
            #kayako_tickets.extend(kApi.get_all(Ticket, d.id))
            #kayako_departments[d.id] = d.title
        #return kayako_departments, kayako_tickets

    #def _kGetTicketUpdates(self, ticketid):
        #return kApi.get_all(TicketPost, ticketid)

    #def _kGetAllStaff(self):
        #staff = kApi.get_all(Staff)
        #kayako_staff = dict()
        #for s in staff:
            #kayako_staff[s.id] = s.firstname + ' ' + s.lastname
        #return kayako_staff

    #def _hGetAllStaff(self):
        #happyfox_staff = dict()
        #for s in getFromHappyFox('staff/').json():
            #happyfox_staff[s['name']] = s['id']
        #return happyfox_staff

    #def _hGetAllContacts(self):
        #happyfox_contacts = dict()
        #pageinfo = getFromHappyFox('users/?size=50&page=1/').json()
        #pagecount = pageinfo['page_info']['page_count']
        #for c in pageinfo['data']:
            #happyfox_contacts[c['name']] = c['id']

        #if pagecount > 1:
            #for page in xrange(2, page_count+1):
                #for c in getFromHappyFox('users/?size=50&page{0}'.format(page)).json()['data']:
                    #happyfox_contacts[c['name']] = c['id']
        #return happyfox_contacts

    #def _kGetAllUsers(self):
        #kayako_users = dict()
        #for ku in self.kayako_users:
            #kayako_users[ku['id']] = ku['fullname']
        #return kayako_users#}}}

    def hCreateAllTickets(self):
        #Tickets and departments/categories from kayako
        #kayako_departments, kayako_tickets = self._kGetAllTickets()

        #Get all categories from hf and put in a dict
        #happyfox_category = dict()
        #for category in getFromHappyFox('categories/').json():
            #happyfox_category[category['name']] = category['id']

        #Get happyfox and kayako staff
        #happyfox_staff, kayako_staff = self._hGetAllStaff(), self._kGetAllStaff()

        #Get happyfox contacts and kayako users
        #happyfox_contacts, kayako_users = self._hGetAllContacts(), self._kGetAllUsers()


        #kayako_departments = getfromshelve('kayako_departments')
        #kayako_tickets = getfromshelve('kayako_tickets')
        #kayako_staff = getfromshelve('kayako_staff')
        #kayako_users = getfromshelve('kayako_users')
        #happyfox_staff = self._hGetAllStaff()
        #happyfox_contacts = self._hGetAllContacts()
        #happyfox_category = dict()
        #for category in getFromHappyFox('categories/').json():
            #happyfox_category[category['name']] = category['id']

        len_kayako_tickets = len(self.k_tickets)
        for i, t in enumerate(self.k_tickets, 1):
            kayako_ticketupdates = kApi.get_all(TicketPost, t.id)
            hf_tkt = dict(created_at=t.creationtime.strftime("%Y-%m-%dT%H:%M:%S"),
                            subject=t.subject,
                            text=kayako_ticketupdates[0].contents,
                            category=self.hf_categories[self.k_departments[t.departmentid]],
                            priority=1,
                            email=t.email,
                            name=t.fullname)
            hf_tkt['t-cf-1'] = t.id

            #Get this tickets attachments
            kayako_ticket_attachments = kApi.get_all(TicketAttachment, t.id)

            #Dict of lists with the attachment tuples
            happyfox_attachments = dict()

            #Attachments to post during ticket creation
            first_update = kayako_ticketupdates[0]
            for attachment in kayako_ticket_attachments:
                if first_update.id == attachment.ticketpostid:
                    m = kApi.get(TicketAttachment, t.id, attachment.id)
                    tempfile = create_temporary_file(m.filename, base64.b64decode(m.contents))
                    tupfile = ('attachments', (m.filename, open(tempfile, 'rb'), m.filetype))
                    if not happyfox_attachments.has_key(first_update.id):
                        happyfox_attachments[first_update.id] = [tupfile]
                    else:
                        happyfox_attachments[first_update.id].append(tupfile)

            hf_tkt_updates = list()
            for ku in kayako_ticketupdates[1:]:
                hf_tkt_update = dict()
                if ku.staffid:
                    hf_tkt_update['staff'] = self.hf_staff[self.k_staff[ku.staffid]]
                else:
                    hf_tkt_update['user'] = self.hf_contacts[self.k_users[str(ku.userid)]]

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

            #Get all the ticket notes
            kayako_ticketnotes = kApi.get_all(TicketNote, t.id)
            hf_pvt_notes = list()
            for kn in kayako_ticketnotes:
                hf_pvt_note = dict()
                hf_pvt_note['staff'] = self.hf_staff[self.k_staff[kn.creatorstaffid]]
                hf_pvt_note['text'] = kn.contents
                hf_pvt_note['timestamp'] = kn.creationdate.strftime("%Y-%m-%dT%H:%M:%S")

                hf_pvt_notes.append(hf_pvt_note)


            #Post the ticket first
            print "Posting ticket {0}/{1}".format(i, len_kayako_tickets)
            endpoint = 'tickets/'
            if happyfox_attachments.has_key(first_update.id):
                response = postToHappyFox(endpoint, hf_tkt, files=happyfox_attachments[first_update.id])
            else:
                response = postToHappyFox(endpoint, hf_tkt)
            ticketid = response.json()['id']

            #Now post the tickets updates
            print "Posting updates of ticket {0}/{1}".format(i, len_kayako_tickets)
            for u in hf_tkt_updates:
                if u.has_key('staff'):
                    endpoint = 'ticket/{0}/staff_update/'.format(ticketid)
                else:
                    endpoint = 'ticket/{0}/user_reply/'.format(ticketid)
                uid = u['id']
                del u['id']
                if happyfox_attachments.has_key(uid):
                    response = postToHappyFox(endpoint, u, files=happyfox_attachments[uid])
                else:
                    postToHappyFox(endpoint, u)

            #Now post all the private notes
            print "Posting private notes of ticket {0}/{1}".format(i, len_kayako_tickets)
            for pn in hf_pvt_notes:
                endpoint = 'ticket/{0}/staff_pvtnote/'.format(ticketid)
                postToHappyFox(endpoint, pn)

            print "Completed {0}/{1}".format(i, len_kayako_tickets)

def create_temporary_file(filename, contents):
    path = os.path.join(tempfile.gettempdir(), "KayakoImport", HF_API_KEY) + os.sep
    if not os.path.exists(path):
        os.makedirs(path)
    with open(path + filename, 'w') as f:
        f.write(contents)
    return path+filename

def newmain():
    hf_contacts = hGetAllContacts()
    hf_categories = hGetAllCategories()
    hf_staff = hGetAllStaff()
    hf_priorities = None
    hf_statuses = None

    k_users = kGetAllUsers()
    #k_departments = kGetAllDepartments()
    k_staff = kGetAllStaff()
    #k_tickets = kGetAllTickets(k_departments)

    k_departments, k_tickets = kGetAllTicketsAndDepartments()

    Tickets(hf_contacts,
                hf_categories,
                hf_staff,
                k_users,
                k_staff,
                k_tickets,
                k_departments).hCreateAllTickets()

def hGetAllCategories():
    happyfox_category = dict()
    for category in getFromHappyFox('categories/').json():
        happyfox_category[category['name']] = category['id']
    return happyfox_category

def hGetAllStaff():
    happyfox_staff = dict()
    for s in getFromHappyFox('staff/').json():
        happyfox_staff[s['name']] = s['id']
    return happyfox_staff

def hGetAllContacts():
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

def kGetAllUsers():
    endpoint = '/Base/User/Filter'
    response = getFromKayako(endpoint)
    users = xmltodict.parse(response.text)['users']['user']
    kayako_users = dict()
    for i, u in enumerate(users, 1):
        ku = dict(u)
        kayako_users[int(ku['id'])] = ku['fullname']
    return kayako_users

#def _kGetAllUsers(self):
    #kayako_users = dict()
    #for ku in self.kayako_users:
        #kayako_users[ku['id']] = ku['fullname']
    #return kayako_users

def kGetAllTicketsAndDepartments():
    depts = kApi.get_all(Department)
    kayako_tickets = list()
    kayako_departments = dict()
    for d in depts:
        kayako_tickets.extend(kApi.get_all(Ticket, d.id))
        kayako_departments[d.id] = d.title
    return kayako_departments, kayako_tickets

#def kGetAllTickets(depts):
    #kayako_tickets = list()
    #for d in depts:
        #kayako_tickets.extend(kApi.get_all(Ticket, d['id'][1]))
    #return kayako_tickets

#def kGetAllDepartments():
    #kayako_departments = dict()
    #depts = kApi.get_all(Department)
    #for d in depts:
        #kayako_departments[d.id] = (d.title, d.id)
    #return kayako_departments

def kGetAllStaff():
    staff = kApi.get_all(Staff)
    kayako_staff = dict()
    for s in staff:
        kayako_staff[s.id] = s.firstname + ' ' + s.lastname
    return kayako_staff

newmain()
#def getfromshelve(varname):
    #import shelve
    #s = shelve.open('../main.hg/tempdata')
    #varvalue = s[varname]
    #s.close()
    #return varvalue

#def putinshelve(varname, varvalue):
    #import shelve
    #s = shelve.open('../main.hg/tempdata')
    #s[varname] = varvalue
    #s.close()


