import logging
import datetime


formatter = '[%(asctime)s] %(levelname)8s --- %(message)s (%(filename)s:%(lineno)s)'
logging.basicConfig(
    filename=f'bot-from-{datetime.datetime.now().date()}.log',
    filemode='w',
    format=formatter,
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.WARNING
)


BOT_TOKEN = "2020786505:AAEf_Hqo_sXIF5xET-SCWTvse1tWjvfTSr0"  # please shu turip tursin :)
MONGO_URL = 'mongodb+srv://gproduct:qwerty2021@cluster0.sjsk4.mongodb.net/chatbot?retryWrites=true&w=majority'  # shu ham :)

# BOT_TOKEN = "5042886538:AAGUs9OQ0Zd9_Nc33HpDX7IkePu3roh4BME"
# MONGO_URL = 'mongodb+srv://vodiylik:vodiylik@cluster0.b18ay.mongodb.net/davraBot?retryWrites=true&w=majority'
