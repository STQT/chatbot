import logging
import datetime
import os

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

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

cities = ("Toshkent", "Andijon", "Buxoro",
          "Jizzax", "Sirdaryo", "Qoraqalpogʻiston",
          "Xorazm", "Navoiy", "Namangan",
          "Fargʻona", "Toshkent v", "Qashqadaryo",
          "Samarqand", "Surxondaryo")

city_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton("Toshkent"),
      KeyboardButton("Andijon"),
      KeyboardButton("Buxoro")
      ],
     [KeyboardButton("Toshkent v"),
      KeyboardButton("Jizzax"),
      KeyboardButton("Sirdaryo")
      ],
     [KeyboardButton("Qashqadaryo"),
      KeyboardButton("Navoiy"),
      KeyboardButton("Namangan")
      ],
     [KeyboardButton("Surxondaryo"),
      KeyboardButton("Qoraqalpogʻiston"),
      KeyboardButton("Samarqand"),
      ],
     [KeyboardButton("Fargʻona"),
      KeyboardButton("Xorazm")
      ],
     ], resize_keyboard=True)

main_menu_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton("☕️ Tasodifiy suhbatdosh")],
        [KeyboardButton("☕ Anketalardan izlash")],
        [KeyboardButton("🔖 Anketa"),
         KeyboardButton("ℹ️ Qo'llanma")]
    ],
    resize_keyboard=True
)

anketa_keyboard = ReplyKeyboardMarkup(
    [
        [
            KeyboardButton("☕️ Suhbatdosh izlash")],
        [
            # KeyboardButton("💣 Anketani o'chirish"),
            KeyboardButton("✏ Bio"),
            KeyboardButton("🗣 Do'stlarga ulashish")],
        [
            KeyboardButton("🏠 Bosh menyu"), ]
    ],
    resize_keyboard=True
)

change_bio_keyboard = ReplyKeyboardMarkup(
    [
        [
            KeyboardButton("✏ Haqimda"),
            KeyboardButton("✏ Jins")],
        [
            KeyboardButton("✏ Kim bilan suxbatlashish?")],
        [
            KeyboardButton("✏ Tahallusni o'zgartirish")],
        [
            KeyboardButton("🖼 Suratni alishtirish")],
        [
            KeyboardButton("🔖 Anketa")]
    ],
    resize_keyboard=True
)


async def like_keyboard(new: bool = False, user_id: int = None) -> InlineKeyboardMarkup:
    if new:  # if Unreaction keyboard
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("👍", callback_data=CallbackData(
                        "yes", "action").new(action=str(user_id))),
                    InlineKeyboardButton("👎", callback_data=CallbackData(
                        "no", "action").new(action=str(user_id)))
                ]
            ],
        )
    else:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("👍", callback_data=CallbackData(
                        "liked", "action").new(action="liked")),
                    InlineKeyboardButton("👎", callback_data=CallbackData(
                        "liked", "action").new(action="liked"))
                ]
            ],
        )


async def send_mail_keyboard(user_id: str = None, cancel: bool = False) -> (InlineKeyboardMarkup, ReplyKeyboardMarkup):
    if cancel:
        return ReplyKeyboardMarkup(
            [
                [KeyboardButton("🚫 Bekor qilish")],
            ],
            resize_keyboard=True
        )
    else:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("📤", callback_data=CallbackData(
                        "mail", "action").new(action=user_id))
                ]
            ],
        )


async def get_message_data_for_fsm(message: types.Message, data: FSMContext.proxy):
    if message.voice:
        data['type'] = 'voice'
        data['voice'] = message.voice.file_id
        data['caption'] = message.caption
        data['caption_entities'] = message.caption_entities
        return data
    elif message.video:
        data['type'] = 'video'
        data['video'] = message.video
        data['caption'] = message.caption
        data['caption_entities'] = message.caption_entities
        return data
    elif message.photo:
        data['type'] = 'photo'
        data['photo'] = message.photo[-1].file_id
        data['caption'] = message.caption
        data['caption_entities'] = message.caption_entities
        return data
    elif message.sticker:
        data['type'] = 'sticker'
        data['sticker'] = message.sticker.file_id
        return data
    elif message.text:
        data['type'] = 'text'
        data['text'] = message.text
        data['entities'] = message.entities
        return data
    elif message.document:
        data['type'] = 'document'
        data['document'] = message.document.file_id
        data['caption'] = message.caption
        data['caption_entities'] = message.caption_entities
        return data


BOT_TOKEN = os.environ.get("davrabot")
MONGO_URL = os.environ.get("davra_db")
