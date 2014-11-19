import tempfile
import os
import hashlib
import random
import base64
import hmac
import string
import json
import sys
import datetime
import re
import chardet
import h2t

from config import (KAYAKO_API_URL,
                    KAYAKO_API_KEY,
                    KAYAKO_SECRET_KEY,
                    HF_API_URL,
                    HF_API_KEY,
                    HF_AUTH_KEY)
try:
    import xmltodict
except ImportError:
    print "xmltodict not found"
    print "try: pip install xmltodict"
try:
    import requests
except ImportError:
    print "requests not found"
    print "try: pip install requests"

try:
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
except ImportError:
    print "kayako not found"
    print "try: pip install kayako"


PHONE_NUMBER_REGEXP = re.compile(r"^[\+]?\d{6,29}$")#{{{

"""
The handle kApi is for communicating with the
Kayako API respectively.
"""
kApi = KayakoAPI(KAYAKO_API_URL, KAYAKO_API_KEY, KAYAKO_SECRET_KEY)
hApi = (HF_API_KEY, HF_AUTH_KEY)#}}}

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
    return response#}}}

def getFromHappyFox(endpoint):#{{{
    return requests.get(HF_API_URL + endpoint, auth=hApi)#}}}

def getFromKayako(endpoint, **args):#{{{
    """
    Makes get requests to the Kayako URL
    """
    salt, signature = getKayakoSignature()
    payload = dict(apikey=KAYAKO_API_KEY, e=endpoint, salt=salt, signature=signature)
    return requests.get(KAYAKO_API_URL, params=payload, **args)#}}}


class Tickets(object):
    def __init__(self, hf_contacts,#{{{
                    hf_categories,
                    hf_staff,
                    hf_status,
                    hf_priority,
                    hf_admin,
                    k_staff,
                    k_tickets,
                    k_status,
                    k_priority,
                    k_departments,
                    fromticket,
                    len_kayako_tickets,
                    logfile,
		    due_date_logfile):

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

        self.fromticket = fromticket
        self.len_kayako_tickets = len_kayako_tickets
        self.logfile = logfile#}}}
        self.due_date_logfile = due_date_logfile#}}}

    def hCreateAllTickets(self):
        for i, t in enumerate(self.k_tickets, self.fromticket):
            print "Getting ticket updates..",
            try:
                kayako_ticketupdates = kApi.get_all(TicketPost, t.id)
                try:
                    self.hf_contacts[t.email]
                except KeyError:
                    response = postToHappyFox('users/', dict(name=t.fullname, email=t.email))
                    newhf_user = response.json()
                    self.hf_contacts[newhf_user['email']] = newhf_user['id']

                first_update = kayako_ticketupdates[0]
                if first_update.ishtml:
                    first_update_content = h2t.html2text(first_update.contents)
                else:
                    first_update_content = first_update.contents
                hf_tkt = dict(created_at=t.creationtime.strftime("%Y-%m-%dT%H:%M:%S"),
                                subject=t.subject,
                                text=first_update_content,
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
                status_assignee_update_time = first_update.dateline + datetime.timedelta(seconds=1)
                status_assignee_update['timestamp'] = status_assignee_update_time.strftime("%Y-%m-%dT%H:%M:%S")

                #Now create the rest of the updates for the tickets
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

                    if ku.ishtml:
                        ku_content = h2t.html2text(ku.contents)
                    else:
                        ku_content = ku.contents
                    hf_tkt_update['text'] = ku_content
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
                print "Posting ticket..",
                endpoint = 'tickets/'
                if happyfox_attachments.has_key(first_update.id):
                    response = postToHappyFox(endpoint, hf_tkt, files=happyfox_attachments[first_update.id])
                else:
                    response = postToHappyFox(endpoint, hf_tkt)
                ticketid = response.json()['id']

                #Post update to set ticket status and assignee to kayako status and assignee
                endpoint = 'ticket/{0}/staff_update/'.format(ticketid)
                postToHappyFox(endpoint, status_assignee_update)

                #Now post the tickets updates
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
                print "notes..",
                for pn in hf_pvt_notes:
                    endpoint = 'ticket/{0}/staff_pvtnote/'.format(ticketid)
                    postToHappyFox(endpoint, pn)

                print "Completed {0}/{1}".format(i, self.len_kayako_tickets)
                successmsg = "Success {0} {1} {2}".format(t.displayid, ticketid, t.resolutiondue)
                due_datemsg = "{0} {1}".format(ticketid, t.resolutiondue)
                self.logfile.write(successmsg+'\n')
                self.due_date_logfile.write(due_datemsg+'\n')
            except Exception as e:
                print "Failed {0}/{1}".format(i, self.len_kayako_tickets)
                errmsg = "Failed {0}. Exception: {1}".format(t.displayid, e)
                self.logfile.write(errmsg+'\n')

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

#TODO: Fix contact custom field
def hGetAllContacts(k_users, log_file):
    def gen_chunks(l, n):
        for i in range(0, len(l), n):
            yield l[i:i+n]

    endpoint = 'users/'
    happyfox_contacts = dict()
    for kusers in gen_chunks(k_users, 100):
        json_kusers = json.dumps(kusers)
        response = postToHappyFox(endpoint,
                        json_kusers,
                        headers={"Content-Type": "application/json"})
        for contact in response.json():
            if 'error' in contact:
                errmsg = 'Failed contact creation for email: %s, Reason: %s' % (contact['email'], contact['error'])
                log_file.write(errmsg+'\n')
            else:
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
        kayako_priority[p.id] = p.title.strip()
    return kayako_priority

def kGetAllStatus():
    statuses = kApi.get_all(TicketStatus)
    kayako_status = dict()
    for s in statuses:
        kayako_status[s.id] = s.title.strip()
    return kayako_status

#TODO: Fix contact custom field
#TODO: Instead of looping for hard-coded times, find the pages and loop over correctly.
def kGetAllUsers():
  marker = None
  kayako_users = list()
  for i in range(0,3):
    if marker:
        endpoint = '/Base/User/Filter/%s/1000' % marker
    else:
        endpoint = '/Base/User/Filter'
    response = getFromKayako(endpoint)
    users = xmltodict.parse(response.text)['users']['user']
    if marker and users:
        users = users[1:]
    print 'USERS COUNT: %s' % len(users)
    for i, u in enumerate(users, 1):
        ku = dict(u)
        emails = ku['email']
        ku_emails = emails.split(',') if type(ku['email']) != list else emails
        for email in ku_emails:
            newuser = dict(name=ku['fullname'].strip(), email=email.strip())
            userphone = ku['phone']
            if userphone:
                userphone = re.sub('[- .]', '', userphone).strip()
                if not PHONE_NUMBER_REGEXP.match(userphone):
                    newuser['c-cf-1'] = userphone
                else:
                    newuser['phones'] = [dict(type='m', number=userphone)]
            kayako_users.append(newuser)
        marker = ku['id']
  print 'FINAL USERS COUNT: %s' % len(kayako_users)
  return kayako_users

def kGetAllDepartments():
    depts = kApi.get_all(Department)
    kayako_departments = dict()
    for d in depts:
        kayako_departments[d.id] = d.title.strip()
    return kayako_departments

def kGetAllTickets(k_status, k_departments):
    """
    Gets only 20 tickets
    """
    class Tkt(object):
        pass

    kayako_tickets = list()
    for d in k_departments:
        endpoint = '/Tickets/Ticket/ListAll/{0}/-1/-1/-1/5/-1/-1/-1'.format(d)
        response = getFromKayako(endpoint)
        tkts = xmltodict.parse(response.text)['tickets']['ticket']
        for t in tkt:
            nt = Tkt()
            for k in t.keys():
                setattr(nt, k, t[k])
            kayako_tickets.append(nt)
        if len(kayako_tickets) >= 20:
            break
    return kayako_tickets
    #kayako_tickets = list()
    #for d in k_departments:
        #for s in k_status.keys():
            #kayako_tickets.extend(kApi.get_all(Ticket, d, ticketstatusid=s))
    #return kayako_tickets

def kGetAllStaff():
    staff = kApi.get_all(Staff)
    kayako_staff = dict()
    for s in staff:
        kayako_staff[s.id] = s.firstname.strip() + ' ' + s.lastname.strip()
    return kayako_staff

def kGetTicketAttachment(ticketid, attachmentid):
    endpoint = '/Tickets/TicketAttachment/{0}/{1}'.format(ticketid, attachmentid)
    response = getFromKayako(endpoint, stream=True)
    a = xmltodict.parse(response.text)['attachments']['attachment']
    fn, ft, c = a['filename'], a['filetype'], a['contents']
    response.close()
    enc_type = chardet.detect(fn)['encoding']
    if enc_type:
        fn = fn.encode(enc_type)
    else:
        fn = str(fn)
    enc_type = chardet.detect(ft)['encoding']
    if enc_type:
        ft = ft.encode(enc_type)
    else:
        ft = str(ft)
    enc_type = chardet.detect(c)['encoding']
    if enc_type:
        c = c.encode(enc_type)
    else:
        c = str(c)

    return (fn, ft, c)

def in_sync(k_dict, hf_dict):
    need_to_create = list()
    for kd in k_dict.values():
        if not hf_dict.get(kd, None):
            need_to_create.append(kd)

    return need_to_create

def requiredHFobjects(objects, plural):
    print "The following {0} need to be created on Happyfox".format(plural)
    for o in objects:
        print o

def newmain():
    fromticket = 1
    if len(sys.argv) == 2:
        fromticket = int(sys.argv[1])
    print "Starting from ticket {0}".format(fromticket)

    """
    Change current directory to the directory of this script.
    This is to ensure that the temporary files are created in
    the directory in which this script is executing
    """
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    if os.path.exists('./tempdata'):
        print "A './tempdata' file exists in the current directory."
        useexisting = raw_input("Using existing './tempdata' file (y/n)\n")
        if useexisting != 'y':
            os.remove('./tempdata')
            print "Deleted './tempdata'"

    """
    Contact and Ticket custom fields
    """
    print "The following customfields are required:"
    print "Ticket CustomField"
    print "     Name: KayakoDisplayID"
    print "     Type: Text"
    print "Contact CustomField"
    print "     Name: PhoneNumber"
    print "     Type: Text"

    if raw_input("Proceed (y/n)?") != 'y':
        sys.exit()

    """
    Kayako Departments and Happyfox Categories
    """
    print "Getting Kayako departments"
    k_departments = getFromShelve('k_departments')
    if not k_departments:
        k_departments = kGetAllDepartments()
        putInShelve('k_departments', k_departments)
    hf_categories = hGetAllCategories()
    to_sync = in_sync(k_departments, hf_categories)
    if to_sync:
        requiredHFobjects(to_sync, 'categories')
        sys.exit()

    """
    Kayako and Happyfox Staff
    """
    print "Getting Kayako staff"
    k_staff = getFromShelve('k_staff')
    if not k_staff:
        k_staff = kGetAllStaff()
        putInShelve('k_staff', k_staff)
    hf_staff, hf_admin = hGetAllStaff()
    to_sync = in_sync(k_staff, hf_staff)
    if to_sync:
        requiredHFobjects(to_sync, 'staff members')
        sys.exit()

    """
    Kayako and Happyfox Statuses
    """
    print "Getting Kayako statuses"
    k_status = getFromShelve('k_status')
    if not k_status:
        k_status = kGetAllStatus()
        putInShelve('k_status', k_status)
    hf_status = hGetAllStatus()
    to_sync = in_sync(k_status, hf_status)
    if to_sync:
        requiredHFobjects(to_sync, 'statuses')
        sys.exit()

    """
    Kayako and Happyfox Priorities
    """
    print "Getting Kayako priorities"
    k_priority = getFromShelve('k_priority')
    if not k_priority:
        k_priority = kGetAllPriority()
        putInShelve('k_priority', k_priority)
    hf_priority = hGetAllPriority()
    to_sync = in_sync(k_priority, hf_priority)
    if to_sync:
        requiredHFobjects(to_sync, 'priorities')
        sys.exit()

    """
    Kayako and Happyfox Users/Contacts
    """
    print "Getting Kayako users"
    k_users = getFromShelve('k_users')
    if not k_users:
        k_users = kGetAllUsers()
        putInShelve('k_users', k_users)
    hf_contacts = getFromShelve('hf_contacts')
    logfile = open('./kayako.log', 'a')
    if not hf_contacts:
        hf_contacts = hGetAllContacts(k_users, logfile)

    """
    Kayako Tickets
    """
    print "Getting Kayako tickets"
    k_tickets = getFromShelve('k_tickets')
    if not k_tickets:
        k_tickets = kGetAllTickets(k_status, k_departments)
        putInShelve('k_tickets', k_tickets)


    len_kayako_tickets = len(k_tickets)
    if fromticket > 1:
        k_tickets = k_tickets[fromticket:]


    due_date_logfile = open('./due_date.log', 'a')
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
                k_departments,
                fromticket,
                len_kayako_tickets,
                logfile,
		due_date_logfile).hCreateAllTickets()
    logfile.close()
    due_date_logfile.close()

def getFromShelve(varname):#{{{
    """
    Returns `None` if varname is not found
    """
    import shelve
    #s = shelve.open('../main.hg/tempdata')
    s = shelve.open('./tempdata')
    varvalue = s.get(varname, None)
    s.close()
    return varvalue

def putInShelve(varname, varvalue):
    import shelve
    s = shelve.open('./tempdata')
    s[varname] = varvalue
    s.close()#}}}


newmain()
