import logging
import datetime
import os


formatter = '[%(asctime)s] %(levelname)8s --- %(message)s (%(filename)s:%(lineno)s)'
logging.basicConfig(
    filename=f'logs/bot-from-{datetime.datetime.now().date()}.log',
    filemode='w',
    format=formatter,
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.WARNING
)

admin_ids = 256665985, 390736292, 531409948, 556739283
group_id = -650304675
channel_urls_dict = ({
    "title": "Мозийга бир назар",
    "link": "https://t.me/+ZwCfAKCjmeFkNmNi",
    "username": "@moziy_nazar"
},
)


BOT_TOKEN = os.environ.get("davrabot")
MONGO_URL = os.environ.get("davra_db")