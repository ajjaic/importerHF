from config import (KAYAKO_API_URL, KAYAKO_API_KEY, KAYAKO_SECRET_KEY)
from kayako import (
        KayakoAPI,
        User,
        Department,
        Ticket)


api = KayakoAPI(KAYAKO_API_URL, KAYAKO_API_KEY, KAYAKO_SECRET_KEY)
import pudb; pu.db
