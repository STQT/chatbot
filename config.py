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
                         "title": "A'zo bo'lish",
                         "link": "https://t.me/+ZwCfAKCjmeFkNmNi",
                         "username": "@moziy_nazar"
                     },
)

ban_seconds = 86400

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
        [KeyboardButton("👩‍🦱 Qiz suhbatdosh izlash")],
        [KeyboardButton("☕ Anketalardan izlash")],
        [KeyboardButton("🔖 Anketa"),
         KeyboardButton("ℹ️ Qo'llanma")]
    ],
    resize_keyboard=True
)

anketa_keyboard = ReplyKeyboardMarkup(
    [
        [
            KeyboardButton("☕️ Tasodifiy suhbatdosh")],
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

vote_cb = CallbackData('vote', 'id', 'action')  # vote:<id>:<action>
liked_cb = CallbackData('liked', 'action')  # liked:liked
confirm_cb = CallbackData('confirm', 'id', 'action')  # confirm:<id>:<action>
mail_cb = CallbackData('mail', 'id', 'action')


async def like_keyboard(new: bool = False, user_id: int = None) -> InlineKeyboardMarkup:
    if new:  # if Unreaction keyboard
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("👍", callback_data=vote_cb.new(id=str(user_id), action="yes")),
                    InlineKeyboardButton("👎", callback_data=vote_cb.new(id=str(user_id), action="no")),
                ]
            ],
        )
    else:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("👍", callback_data=liked_cb.new(action="liked")),
                    InlineKeyboardButton("👎", callback_data=liked_cb.new(action="liked"))
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
                    InlineKeyboardButton("📤 Xabar yozish", callback_data=mail_cb.new(id=user_id, action="mail"))
                ]
            ],
        )


async def get_message_data_for_fsm(message: types.Message, data: FSMContext.proxy):
    if message.forward_from_chat:
        data['type'] = 'forward'
        data['message'] = message
        return data
    elif message.text:
        data['type'] = 'text'
        data['text'] = message.text
        data['entities'] = message.entities
        return data
    elif message.photo:
        data['type'] = 'photo'
        data['photo'] = message.photo[-1].file_id
        data['caption'] = message.caption
        data['caption_entities'] = message.caption_entities
        return data
    elif message.voice:
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
    elif message.sticker:
        data['type'] = 'sticker'
        data['sticker'] = message.sticker.file_id
        return data
    elif message.document:
        data['type'] = 'document'
        data['document'] = message.document.file_id
        data['caption'] = message.caption
        data['caption_entities'] = message.caption_entities
        return data


BOT_TOKEN = os.environ.get("davrabot")
MONGO_URL = os.environ.get("davra_db")
