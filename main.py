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


k_api = KayakoAPI(KAYAKO_API_URL, KAYAKO_API_KEY, KAYAKO_SECRET_KEY)
h_api = dict(auth=(HF_API_KEY, HF_AUTH_KEY))

resp = requests.get(HF_API_URL+'users/', params={'size':'10', 'page':'1'}, **hapi)
print resp.json()

class Contact(object):
    def k_get_contacts():
        k_api.get_all(User)
        pass
    def h_get_contacts():
        pass
