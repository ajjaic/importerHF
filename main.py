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
                    TicketNote,
                    TicketStatus,
                    TicketPriority)
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

def postToHappyFox(endpoint, payload, headers=None, files=None):#{{{
    """
    Makes post requests to the happyfox URL
    """
    url = HF_API_URL + endpoint
    if not files:
        if headers:
            response = requests.post(url,
                        data=payload,
                        headers=headers,
                        auth=(HF_API_KEY, HF_AUTH_KEY))
        else:
            response = requests.post(url,
                        data=payload,
                        auth=(HF_API_KEY, HF_AUTH_KEY))
    else:
        response = requests.post(url,
                    data=payload,
                    files=files,
                    auth=(HF_API_KEY, HF_AUTH_KEY))
    return response

def getFromHappyFox(endpoint):
    return requests.get(HF_API_URL + endpoint, auth=hApi)#}}}

def getFromKayako(endpoint, **args):#{{{
    """
    Makes get requests to the Kayako URL
    """
    salt, signature = getKayakoSignature()
    payload = dict(apikey=KAYAKO_API_KEY, e=endpoint, salt=salt, signature=signature)
    return requests.get(KAYAKO_API_URL, params=payload, **args)#}}}


class Tickets(object):
    def __init__(self, hf_contacts,
                    hf_categories,
                    hf_staff,
                    hf_status,
                    hf_priority,
                    hf_admin,
                    k_staff,
                    k_tickets,
                    k_status,
                    k_priority,
                    k_departments):

        self.hf_contacts = hf_contacts
        self.hf_categories = hf_categories
        self.hf_staff = hf_staff
        self.hf_status = hf_status
        self.hf_priority = hf_priority
        self.hf_admin = hf_admin

        self.k_staff = k_staff
        self.k_tickets = k_tickets
        self.k_status = k_status
        self.k_priority = k_priority
        self.k_departments = k_departments

    def hCreateAllTickets(self):

        len_kayako_tickets = len(self.k_tickets)
        for i, t in enumerate(self.k_tickets, 1):
            print "Getting ticket updates..",
            kayako_ticketupdates = kApi.get_all(TicketPost, t.id)
            try:
                self.hf_contacts[t.email]
            except KeyError:
                response = postToHappyFox('users/', dict(name=t.fullname, email=t.email))
                newhf_user = response.json()
                self.hf_contacts[newhf_user['email']] = newhf_user['id']

            hf_tkt = dict(created_at=t.creationtime.strftime("%Y-%m-%dT%H:%M:%S"),
                            subject=t.subject,
                            text=kayako_ticketupdates[0].contents,
                            category=self.hf_categories[self.k_departments[t.departmentid]],
                            priority=self.hf_priority[self.k_priority[t.ticketpriorityid]],
                            user=self.hf_contacts[t.email])
            hf_tkt['t-cf-1'] = t.displayid

            #Get this tickets attachments
            print "attachments..",
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

            #Create update to set ticket status and assignee to kayako status and assignee
            status=self.hf_status[self.k_status[t.statusid]]
            if self.k_staff.has_key(t.ownerstaffid):
                assignee = self.hf_staff[self.k_staff[t.ownerstaffid]]
                status_assignee_update = dict(status=status, staff=self.hf_admin['id'], assignee=assignee)
            else:
                status_assignee_update = dict(status=status, staff=self.hf_admin['id'])

            hf_tkt_updates = list()
            for ku in kayako_ticketupdates[1:]:
                hf_tkt_update = dict()
                if ku.staffid:
                    hf_tkt_update['staff'] = self.hf_staff[self.k_staff[ku.staffid]]
                else:
                    try:
                        self.hf_contacts[ku.email]
                    except KeyError:
                        response = postToHappyFox('users/', dict(name=ku.fullname, email=ku.email))
                        newhf_user = response.json()
                        self.hf_contacts[newhf_user['email']] = newhf_user['id']
                    hf_tkt_update['user'] = self.hf_contacts[ku.email]

                hf_tkt_update['text'] = ku.contents
                hf_tkt_update['timestamp'] = ku.dateline.strftime("%Y-%m-%dT%H:%M:%S")
                hf_tkt_update['id'] = ku.id

                hf_tkt_updates.append(hf_tkt_update)


                for attachment in kayako_ticket_attachments:
                    if ku.id == attachment.ticketpostid:
                        filename, filetype, contents = kGetTicketAttachment(t.id, attachment.id)
                        tempfile = create_temporary_file(filename, base64.b64decode(contents))
                        tupfile = ('attachments', (filename, open(tempfile, 'rb'), filetype))
                        if not happyfox_attachments.has_key(ku.id):
                            happyfox_attachments[ku.id] = [tupfile]
                        else:
                            happyfox_attachments[ku.id].append(tupfile)

            #Get all the ticket notes
            print "notes.",
            kayako_ticketnotes = kApi.get_all(TicketNote, t.id)
            hf_pvt_notes = list()
            for kn in kayako_ticketnotes:
                hf_pvt_note = dict()
                hf_pvt_note['staff'] = self.hf_staff[self.k_staff[kn.creatorstaffid]]
                hf_pvt_note['text'] = kn.contents
                hf_pvt_note['timestamp'] = kn.creationdate.strftime("%Y-%m-%dT%H:%M:%S")

                hf_pvt_notes.append(hf_pvt_note)


            #Post the ticket first
            #print "Posting ticket {0}/{1}".format(i, len_kayako_tickets)
            print "Posting ticket..",
            endpoint = 'tickets/'
            if happyfox_attachments.has_key(first_update.id):
                response = postToHappyFox(endpoint, hf_tkt, files=happyfox_attachments[first_update.id])
            else:
                response = postToHappyFox(endpoint, hf_tkt)
            ticketid = response.json()['id']

            #Post update to set ticket status and assignee to kayako status and assignee
            #status=self.hf_status[self.k_status[t.statusid]]
            #assignee = self.hf_staff[self.k_staff[t.ownerstaffid]]
            #status_assignee_update = dict(status=status, staff=self.hf_admin['id'], assignee=assignee)
            endpoint = 'ticket/{0}/staff_update/'.format(ticketid)
            postToHappyFox(endpoint, status_assignee_update)

            #Now post the tickets updates
            #print "Posting updates of ticket {0}/{1}".format(i, len_kayako_tickets)
            print "updates..",
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
            #print "Posting private notes of ticket {0}/{1}".format(i, len_kayako_tickets)
            print "notes..",
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


def hGetAllCategories():
    happyfox_category = dict()
    for category in getFromHappyFox('categories/').json():
        happyfox_category[category['name']] = category['id']
    return happyfox_category

def hGetAllStaff():
    happyfox_staff = dict()
    admin = None
    for s in getFromHappyFox('staff/').json():
        happyfox_staff[s['name']] = s['id']
        if s['is_account_admin']:
            admin = s
    return happyfox_staff, admin

def hGetAllContacts(k_users):
    def gen_chunks(l, n):
        for i in range(0, len(l), n):
            yield l[i:i+n]

    endpoint = 'users/'
    happyfox_contacts = dict()
    for kusers in gen_chunks(k_users, 100):
        response = postToHappyFox(endpoint,
                        json.dumps(kusers),
                        headers={"Content-Type": "application/json"})
        for contact in response.json():
            happyfox_contacts[contact['email']] = contact['id']
    return happyfox_contacts

def hGetAllStatus():
    happyfox_status = dict()
    for s in getFromHappyFox('statuses/').json():
        happyfox_status[s['name']] = s['id']
    return happyfox_status

def hGetAllPriority():
    happyfox_priority = dict()
    for p in getFromHappyFox('priorities/').json():
        happyfox_priority[p['name']] = p['id']
    return happyfox_priority

def kGetAllPriority():
    priorities = kApi.get_all(TicketPriority)
    kayako_priority = dict()
    for p in priorities:
        kayako_priority[p.id] = p.title
    return kayako_priority

def kGetAllStatus():
    statuses = kApi.get_all(TicketStatus)
    kayako_status = dict()
    for s in statuses:
        kayako_status[s.id] = s.title
    return kayako_status

def kGetAllUsers():
    endpoint = '/Base/User/Filter'
    response = getFromKayako(endpoint)
    users = xmltodict.parse(response.text)['users']['user']

    kayako_users = list()
    for i, u in enumerate(users, 1):
        ku = dict(u)
        emails = ku['email']
        ku_emails = emails.split(',') if type(ku['email']) != list else emails
        for email in ku_emails:
            kayako_users.append(dict(name=ku['fullname'], email=email))
    return kayako_users

def kGetAllTicketsAndDepartments(k_status):
    depts = kApi.get_all(Department)
    kayako_tickets = list()
    kayako_departments = dict()
    for d in depts:
        for s in k_status.keys():
            kayako_tickets.extend(kApi.get_all(Ticket, d.id, ticketstatusid=s))
        kayako_departments[d.id] = d.title
    return kayako_departments, kayako_tickets

def kGetAllStaff():
    staff = kApi.get_all(Staff)
    kayako_staff = dict()
    for s in staff:
        kayako_staff[s.id] = s.firstname + ' ' + s.lastname
    return kayako_staff

def kGetTicketAttachment(ticketid, attachmentid):
    endpoint = '/Tickets/TicketAttachment/{0}/{1}'.format(ticketid, attachmentid)
    response = getFromKayako(endpoint, stream=True)
    a = xmltodict.parse(response.text)['attachments']['attachment']
    fn, ft, c = a['filename'], a['filetype'], a['contents']
    response.close()
    return (fn, ft, c)

def newmain():
    k_users = kGetAllUsers()
    hf_contacts = hGetAllContacts(k_users)

    hf_categories = hGetAllCategories()
    hf_staff, hf_admin = hGetAllStaff()
    hf_status = hGetAllStatus()
    hf_priority = hGetAllPriority()

    k_staff = kGetAllStaff()
    k_status = kGetAllStatus()
    k_priority = kGetAllPriority()
    k_departments, k_tickets = kGetAllTicketsAndDepartments(k_status)

    #putinshelve('hf_contacts', hf_contacts)
    #putinshelve('hf_categories', hf_categories)
    #putinshelve('hf_staff', hf_staff)
    #putinshelve('hf_status', hf_status)
    #putinshelve('hf_priority', hf_priority)
    #putinshelve('hf_admin', hf_admin)
    #putinshelve('k_staff', k_staff)
    #putinshelve('k_status', k_status)
    #putinshelve('k_priority', k_priority)
    #putinshelve('k_departments', k_departments)
    #putinshelve('k_tickets', k_tickets)

    #hf_contacts = getfromshelve('hf_contacts')
    #hf_categories = getfromshelve('hf_categories')
    #hf_staff = getfromshelve('hf_staff')
    #hf_status = getfromshelve('hf_status')
    #hf_priority = getfromshelve('hf_priority')
    #hf_admin = getfromshelve('hf_admin')
    #k_staff = getfromshelve('k_staff')
    #k_status = getfromshelve('k_status')
    #k_priority = getfromshelve('k_priority')
    #k_departments = getfromshelve('k_departments')
    #k_tickets = getfromshelve('k_tickets')

    Tickets(hf_contacts,
                hf_categories,
                hf_staff,
                hf_status,
                hf_priority,
                hf_admin,
                k_staff,
                k_tickets,
                k_status,
                k_priority,
                k_departments).hCreateAllTickets()

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

newmain()
