import asyncio
import datetime
import logging

import admin_commands
import config

from config import BOT_TOKEN, MONGO_URL

import typing
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import BotBlocked, BotKicked, UserDeactivated, Throttled, MessageNotModified
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from pymongo import MongoClient


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

cluster = MongoClient(MONGO_URL)
collqueue = cluster.chatbot.queue
collusers = cluster.chatbot.users
collchats = cluster.chatbot.chats
collrefs = cluster.chatbot.refs
collprchats = cluster.chatbot.prchats
collprchatsqueue = cluster.chatbot.prchatsque
colladmin = cluster.chatbot.admin
collbans = cluster.chatbot.bans

DEFAULT_MAN_PHOTO = "AgACAgIAAxkBAAERnQliI7sTh_4hYOFm2WU9llpkq005xwACLroxG2jSGUmjORqFgslO2wEAAwIAA20AAyME"
DEFAULT_WOMAN_PHOTO = "AgACAgIAAxkBAAERnQFiI7ronfAEFK0tBXj9U3fBPceixwACMLoxG2jSGUkBxYECSA2mwQEAAwIAA20AAyME"


class SetBio(StatesGroup):
    finding = State()
    user_bio = State()
    gender = State()
    nickname = State()
    photo = State()


class SetRegBio(StatesGroup):
    finding = State()
    user_bio = State()
    gender = State()
    referal = State()
    city = State()
    photo = State()


class SetPost(StatesGroup):
    post = State()
    inactive_post = State()


class SetReport(StatesGroup):
    report = State()


class Anketa(StatesGroup):
    user_id = State()


async def handler_throttled(message: types.Message, **kwargs):
    # await bot.send_message(message.from_user.id, "Qayta qayta yozavermang, biroz kutib yozing")
    await message.answer("Qayta qayta yozavermang, biroz kutib yozing")


async def insert_db_prque(sender_id: int, tg_id: str, like: bool = False):
    collprchatsqueue.insert_one({
        "sender": sender_id,
        "accepter": int(tg_id),
        "like": like
    })
    return True


async def get_random_boy_anketa(liked_user_list):
    finded_docs = collusers.find({"gender": {"$nin": ["👩‍ Ayol kishi"]}})
    for i in finded_docs:
        if i and i.get('_id', None) not in liked_user_list and i.get('status', True):
            return i


async def get_random_girl_anketa(liked_user_list):
    finded_docs = collusers.find({"gender": {"$in": ["👩‍ Ayol kishi"]}})
    for i in finded_docs:
        if i and i.get('_id', None) not in liked_user_list and i.get('status', True):
            return i


async def send_reaction_func(sender_id: int, callback_data: typing.Dict[str, str]):
    tg_id = callback_data['id']
    action = callback_data['action']
    if action == "yes":
        try:
            sender_col = collusers.find_one({"_id": sender_id})
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton("👍",
                                             callback_data=config.confirm_cb.new(id=str(sender_id), action="confirm")),
                        InlineKeyboardButton("👎",
                                             callback_data=config.confirm_cb.new(id=str(sender_id), action="refuse"))
                    ]
                ],
            )
            photo = sender_col.get("photo", None)
            if not photo:
                photo = DEFAULT_WOMAN_PHOTO if sender_col.get("gender", None) == "👩‍ Ayol kishi" else DEFAULT_MAN_PHOTO
            text = "*Sizga so'rov keldi*\n" \
                   "Foydalanuvchi: {}\n" \
                   "Bio: {}\n" \
                   "Jins: {}".format(sender_col.get("nickname"), sender_col.get("bio"),
                                     sender_col.get("gender", "Ma'lum emas"))
            await bot.send_photo(int(tg_id), photo, text, parse_mode="Markdown", reply_markup=keyboard)
            await insert_db_prque(sender_id, tg_id, like=True)
        except Exception as e:
            logging.error(f"Error: {e}")
            await admin_commands.user_blocked_with_posting(int(tg_id))

    else:
        await insert_db_prque(sender_id, tg_id)


async def search_random_anketa(user_id: int):
    acc = collusers.find_one({"_id": user_id})
    liked_user_list = [user_id, ]

    for i in collprchatsqueue.find({"sender": user_id}):
        liked_user_list.append(i["accepter"])
    if acc.get("gender", None) == "👩‍ Ayol kishi":
        finded_doc = await get_random_boy_anketa(liked_user_list)
    else:
        finded_doc = await get_random_girl_anketa(liked_user_list)
    return finded_doc


async def send_new_anketa(user_id: int):
    find_doc = await search_random_anketa(user_id)  # noqa
    if find_doc:
        text = "Foydalanuvchi: {}\n" \
               "Bio: {}\n" \
               "Jins: {}".format(find_doc.get("nickname"), find_doc.get("bio"),
                                 find_doc.get("gender", "Ma'lum emas"))
        photo = find_doc.get("photo", None)
        if not photo:
            photo = DEFAULT_WOMAN_PHOTO if find_doc.get("gender", None) == "👩‍ Ayol kishi" else DEFAULT_MAN_PHOTO
        return text, photo, find_doc.get("_id")
    else:
        return "Hech qanday foydalanuvchi mavjud emas", DEFAULT_MAN_PHOTO, None


async def send_message_for_tg_id(message: types.Message, tg_id: int, anketa: bool = True, nickname: str = None):
    user_nickname = None
    reply = None

    # check parameter anketa
    if anketa and nickname:
        user_nickname = "Foydalanuvchi *{}* dan xat:\n".format(nickname)
        reply = await config.send_mail_keyboard(message.from_user.id)

    if message.text:
        await bot.send_message(chat_id=tg_id, text=(user_nickname + message.text) if user_nickname else message.text,
                               entities=message.entities, reply_markup=reply, parse_mode="Markdown")
    elif message.voice:
        await bot.send_voice(chat_id=tg_id, voice=message.voice.file_id,
                             caption=message.caption,
                             caption_entities=message.caption_entities,
                             reply_markup=reply, parse_mode="Markdown")
    elif message.video:
        await bot.send_video(chat_id=tg_id, video=message.video,
                             caption=message.caption,
                             caption_entities=message.caption_entities,
                             reply_markup=reply, parse_mode="Markdown")
    elif message.photo:
        await bot.send_photo(chat_id=tg_id, photo=message.photo[-1].file_id,
                             caption=message.caption,
                             caption_entities=message.caption_entities,
                             reply_markup=reply, parse_mode="Markdown")
    elif message.sticker:
        if anketa:
            await bot.send_message(chat_id=tg_id, text=f"Ushbu *{nickname}* foydalanuvchi sizga stiker jo'natdi",
                                   parse_mode="Markdown")
        await bot.send_sticker(chat_id=tg_id, sticker=message.sticker.file_id)

    elif message.document:
        await bot.send_document(chat_id=tg_id, document=message.document.file_id,
                                caption_entities=message.caption_entities,
                                caption=message.caption,
                                reply_markup=reply, parse_mode="Markdown")


async def confirm_pr_chat_users(first_id: int, second_id: int):
    collprchats.insert_one({
        "first_id": first_id,
        "second_id": second_id})


@dp.message_handler(commands="main_menu")
async def menu(message: (types.Message, types.CallbackQuery)):
    keyboard = config.main_menu_keyboard
    await bot.send_message(chat_id=message.from_user.id, text="🏠 Bosh menyu", reply_markup=keyboard)


@dp.message_handler(commands="start")
@dp.throttled(on_throttled=handler_throttled, rate=2)
async def start_menu(message: types.Message):
    keyboard = config.main_menu_keyboard
    if collusers.count_documents({"_id": message.from_user.id}) == 0:
        if len(message.text.split()) == 2 and message.from_user.id != int(message.text.split()[1]) and \
                collrefs.count_documents({"_id": int(message.text.split()[1])}) == 0:
            # 1. Check start ref ID
            # 2. Check tg self user ID
            # 3. Check is there ref user ID in DB
            collrefs.insert_one(
                {
                    "_id": message.from_user.id,
                    "_ref": int(message.text.split()[1])
                }
            )
            collusers.update_one({"_id": int(message.text.split()[1])}, {
                "$inc": {"balance": 1}})
            await account_registration_act(message)
        else:
            await account_registration_act(message)
    elif collusers.count_documents({"_id": message.from_user.id, "status": False}) == 1:
        collusers.update_one({"_id": message.from_user.id}, {"$set": {"status": True}})
        await message.answer("🏠 Bosh menyu", reply_markup=keyboard)
    else:
        collusers.update_one({"_id": message.from_user.id}, {"$set": {"status": True}})
        await message.answer("🏠 Bosh menyu", reply_markup=keyboard)


@dp.message_handler(commands=["anketa", "set_bio", "new_bio", "about_me"])
async def user_bio(message: types.Message):
    if collusers.count_documents({"_id": message.from_user.id}) == 0:
        await account_user(message)
    else:
        keyboard = config.change_bio_keyboard
        await message.answer("Qaysi bo'limni o'zgartirishni istaysiz?", reply_markup=keyboard)


@dp.message_handler(commands=["haqimda", "me_bio"])
async def user_bio_change(message: types.Message):
    if collusers.count_documents({"_id": message.from_user.id}) == 0:
        await account_user(message)
    else:
        await SetBio.user_bio.set()
        await message.answer("Iltimos, qisqacha o'zingiz haqingizda yozing")


@dp.message_handler(commands=["search_anketa"])
async def search_anketa(message: types.Message):
    # sending first (new) anketa
    text, photo, tg_id = await send_new_anketa(message.from_user.id)
    if tg_id:
        keyboard = await config.like_keyboard(new=True, user_id=tg_id)
        await message.answer_photo(photo=photo, caption=text, reply_markup=keyboard)
    else:
        await message.answer_photo(photo=photo, caption=text)


@dp.message_handler(commands=["jins", "set_gender", "new_gender", "about_gender"])
async def user_gender(message: types.Message):
    if collusers.count_documents({"_id": message.from_user.id}) == 0:
        await account_user(message)
    else:
        await SetBio.gender.set()
        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("👨‍ Yigit kishi"),
              KeyboardButton("👩‍ Ayol kishi"),
              ]], resize_keyboard=True, one_time_keyboard=True)
        await message.answer("Iltimos, jinsingizni tanlang", reply_markup=keyboard)


@dp.message_handler(commands=["qidiruv_jins", "set_finding", "new_finding", "about_finding"])
async def user_finding(message: types.Message):
    if collusers.count_documents({"_id": message.from_user.id}) == 0:
        await account_user(message)
    else:
        await SetBio.finding.set()
        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("👨‍ Yigit kishi"),
              KeyboardButton("👩‍ Ayol kishi"),
              ]], resize_keyboard=True, one_time_keyboard=True)
        await message.answer("Iltimos, kimlar bilan suhbat qurishingizni tanlang", reply_markup=keyboard)


@dp.message_handler(commands=["tahallus", "set_nickname", "new_nickname", "about_nickname"])
async def user_tahallus(message: types.Message):
    if collusers.count_documents({"_id": message.from_user.id}) == 0:
        await account_user(message)
    else:
        await SetBio.nickname.set()
        await message.answer("Iltimos, o'z tahallusingizni yozing")


@dp.message_handler(commands=["photo_set", "photo", "set_photo"])
async def user_photo(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("✖️Bekor qilish"),
          ]], resize_keyboard=True, one_time_keyboard=True)
    if collusers.count_documents({"_id": message.from_user.id}) == 0:
        await account_user(message)
    else:
        await SetBio.photo.set()
        await message.answer("Iltimos, bironta siz bilan bog'liq rasm yuboring", reply_markup=keyboard)


@dp.message_handler(state=SetBio.nickname)
async def process_set_nickname(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["nickname"] = message.text
        collusers.update_one({"_id": message.from_user.id}, {
            "$set": {"nickname": data["nickname"]}})
        await message.answer("Ma'lumotlar saqlandi")
        await state.finish()
    await menu(message)


@dp.message_handler(state=SetBio.user_bio)
async def process_set_bio(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text:
            data["user_bio"] = message.text
            collusers.update_one({"_id": message.from_user.id}, {
                "$set": {"bio": data["user_bio"]}})

            await message.answer("Ma'lumotlar saqlandi")
            await state.finish()
            await menu(message)
        else:
            await message.answer("Iltimos matn formatda yozing!")


@dp.message_handler(state=SetBio.finding)
async def process_set_finding(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["finding"] = message.text
        if data['finding'] == "👨‍ Yigit kishi":
            collusers.update_one({"_id": message.from_user.id}, {
                "$set": {"finding": "👨‍ Yigit kishi"}})
        elif data['finding'] == '👩‍ Ayol kishi':
            collusers.update_one({"_id": message.from_user.id}, {
                "$set": {"finding": "👩‍ Ayol kishi"}
            })
        else:
            collusers.update_one({"_id": message.from_user.id}, {
                "$set": {"finding": "👤 Muhim emas"}
            })

        await message.answer("Ma'lumotlar saqlandi")
        await state.finish()
        await account_user(message)


@dp.message_handler(state=SetBio.gender)
async def process_set_gender(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["gender"] = message.text
        if data['gender'] == "👨‍ Yigit kishi":
            collusers.update_one({"_id": message.from_user.id}, {
                "$set": {"gender": "👨‍ Yigit kishi"}})
        elif data['gender'] == '👩‍ Ayol kishi':
            collusers.update_one({"_id": message.from_user.id}, {
                "$set": {"gender": "👩‍ Ayol kishi"}
            })
        else:
            await SetBio.gender.set()
            keyboard = ReplyKeyboardMarkup(
                [[KeyboardButton("👨‍ Yigit kishi"),
                  KeyboardButton("👩‍ Ayol kishi"),
                  ]], resize_keyboard=True, one_time_keyboard=True)
            await message.answer("Noto'g'ri kiritdingiz", reply_markup=keyboard)
            return True

        await message.answer("Ma'lumotlar saqlandi")
        await state.finish()
        await account_user(message)


@dp.message_handler(state=SetBio.photo, content_types=["photo", "text"])
async def process_set_photo(message: types.Message, state: FSMContext):
    if message.text == "✖️Bekor qilish":
        await state.finish()
        await message.answer("Bekor qilindi")
        return await menu(message)
    elif message.text:
        return await message.answer("Iltimos faqat rasm yuboring yoki bekor qiling")
    async with state.proxy() as data:
        data["user_photo"] = message.photo[-1].file_id
        collusers.update_one({"_id": message.from_user.id}, {
            "$set": {"photo": data["user_photo"]}})

        await message.answer("Ma'lumotlar saqlandi")
        await state.finish()
        await menu(message)


@dp.message_handler(commands=["ref_link"])
async def referal_link(message: types.Message):
    text = "Do'stlaringizga ulashing va balansingizni to'ldiring\n" \
           "Sizning havolangiz: \n\n" \
           f"t.me/davra_bot/?start={message.from_user.id}"
    await message.answer(text)


@dp.message_handler(commands=["account"])
async def account_user(message: types.Message):
    if collusers.count_documents({"_id": message.from_user.id}) == 0:
        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("📝 Ro'yxatdan o'tish")]], resize_keyboard=True, one_time_keyboard=True)
        await message.answer("Siz tizimda hali ro'yxatdan o'tmagansiz", reply_markup=keyboard)
    else:
        acc = collusers.find_one({"_id": message.from_user.id})
        text = f"👤Tahallusi: {acc.get('nickname', 'Mavjud emas')}\n" \
               f"💵 Referal: {acc.get('balance', 'Noaniq')}\n" \
               f"️Reyting: {acc.get('reputation', 'Noaniq')}\n" \
               f"📝Bio: {acc.get('bio', 'Noaniq')}\n" \
               f"👫Jins: {acc.get('gender', 'Noaniq')}\n" \
               f"👫Qidiruv: {acc.get('finding', 'Noaniq')}"
        keyboard = config.anketa_keyboard
        photo = acc.get("photo", None)
        if not photo:
            photo = DEFAULT_WOMAN_PHOTO if acc.get("gender", None) == "👩‍ Ayol kishi" else DEFAULT_MAN_PHOTO
        # await message.answer(text, reply_markup=keyboard)
        await message.answer_photo(photo, text, reply_markup=keyboard)


@dp.message_handler(commands=["anketani", "remove_acc", "remove_account"])
async def remove_account_act(message: types.Message):
    if collusers.count_documents({"_id": message.from_user.id}) != 0:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("✅ Roziman", callback_data=CallbackData(
                        "choice", "action").new(action="remove")),
                    InlineKeyboardButton("❌ Rozimasman", callback_data=CallbackData(
                        "choice", "action").new(action="cancel"))
                ]
            ],
            one_time_keyboard=True
        )

        await message.answer("Siz rostdan ham anketangizni o'chirmoqchimisiz? 🤔", reply_markup=keyboard)
    else:
        await message.answer("Sizning hali anketangiz yo'qku 😁")
        await menu(message)


@dp.message_handler(commands=["reg", "registration"])
async def account_registration_act(message: types.Message):
    if collusers.count_documents({"_id": message.from_user.id}) == 0:
        collusers.insert_one(
            {
                "_id": message.from_user.id,
                "nickname": message.from_user.first_name,
                "balance": 0,
                "reputation": 0,
                "bio": "Tarmoqdagi foydalanuvchilardan biri",
            }
        )
        await SetRegBio.gender.set()
        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("👨‍ Yigit kishi"),
              KeyboardButton("👩‍ Ayol kishi"),
              ]], resize_keyboard=True, one_time_keyboard=True)
        await message.answer(f"Salom, {message.from_user.full_name}\nJinsingiz?", reply_markup=keyboard)
    else:
        await message.answer("Siz tizimda allaqachon anketa yaratgansiz 😉")
        await account_user(message)


@dp.message_handler(commands=["post", "posting"])
async def send_post_act(message: types.Message):
    if message.from_user.id in config.admin_ids:
        await SetPost.post.set()
        await message.answer("Iltimos menga kerakli xabarni yozing")
    else:
        await message.answer("Bunday buyruq botda mavjud emas!")


@dp.message_handler(state=SetPost.post, content_types=["text", "sticker", "photo", "voice", "document", "video"])
async def process_send_post(message: types.Message, state: FSMContext):
    if message.text == "☑️Yuborish":
        data = await state.get_data()
        users = await admin_commands.get_all_active_users()
        sending = await admin_commands.send_post_all_users(data, users)
        if sending:
            await message.answer("Barchaga post muvaffaqiyatli yuborildi.")
        await state.finish()
        await menu(message)
    elif message.text == "✖️Bekor qilish":
        await state.finish()
        await message.answer("Bekor qilindi")
        await menu(message)
    elif message.text == "☑️Faol emaslarga":
        data = await state.get_data()
        users = await admin_commands.get_all_inactive_users()
        sending = await admin_commands.send_post_all_users(data, users)
        if sending:
            await message.answer("Faol emaslarga post muvaffaqiyatli yuborildi.")
        await state.finish()
        await menu(message)
    else:
        async with state.proxy() as data:
            await config.get_message_data_for_fsm(message, data)
            await send_message_for_tg_id(message, message.from_user.id)
            # await state.finish()
            keyboard = ReplyKeyboardMarkup(
                [[KeyboardButton("☑️Yuborish"), KeyboardButton("☑️Faol emaslarga"),
                  KeyboardButton("✖️Bekor qilish"),
                  ]], resize_keyboard=True, one_time_keyboard=True)
            await message.answer("Yuboraylikmi?", reply_markup=keyboard)


@dp.message_handler(state=SetRegBio.user_bio)
async def process_set_bio_reg(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["user_bio"] = message.text
        collusers.update_one({"_id": message.from_user.id}, {
            "$set": {"bio": data["user_bio"]}})

        # await message.answer("Ma'lumotlar saqlandi")
        # await state.finish()
        await SetRegBio.city.set()
        keyboard = config.city_keyboard
        await message.answer("Iltimos, qayerdanligingizni ko'rsating", reply_markup=keyboard)


@dp.message_handler(commands=["city", "shaxar"])
async def process_set_city(message: types.Message):
    await SetRegBio.city.set()
    keyboard = config.city_keyboard
    await message.answer("Iltimos, qayerdanligingizni ko'rsating", reply_markup=keyboard)


@dp.message_handler(state=SetRegBio.gender)
async def process_set_gender_reg(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["gender"] = message.text
        if data['gender'] == "👨‍ Yigit kishi":
            collusers.update_one({"_id": message.from_user.id}, {
                "$set": {"gender": "👨‍ Yigit kishi"}})
        elif data['gender'] == '👩‍ Ayol kishi':
            collusers.update_one({"_id": message.from_user.id}, {
                "$set": {"gender": "👩‍ Ayol kishi"}
            })
        else:
            await SetRegBio.gender.set()
            keyboard = ReplyKeyboardMarkup(
                [[KeyboardButton("👨‍ Yigit kishi"),
                  KeyboardButton("👩‍ Ayol kishi"),
                  ]], resize_keyboard=True, one_time_keyboard=True)
            await message.answer("Noto'g'ri kiritdingiz", reply_markup=keyboard)
            return True

        # await message.answer("Ma'lumotlar saqlandi")
        # await state.finish()  # Finished this
        await SetRegBio.user_bio.set()
        await message.answer(f"Iltimos o'zingiz haqingizda qisqacha ma'lumot bering")


@dp.message_handler(state=SetRegBio.city)
async def process_set_city_reg(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["city"] = message.text
        if data['city'] not in config.cities:
            await message.answer("Iltimos, mavjud shaxarlardan tanlang")
            await SetRegBio.city.set()
        else:
            collusers.update_one({"_id": message.from_user.id}, {
                "$set": {"city": data['city']}
            })
            await message.answer("Ma'lumotlar saqlandi")
            await state.finish()
            await menu(message)


@dp.message_handler(commands=["search_user", "searchuser"])
async def search_user_act(message: types.Message):
    user_follow_act = await admin_commands.is_authenticated(message)
    if user_follow_act:
        if message.chat.type == "private":
            # if collusers.count_documents({"_id": message.from_user.id}) == 0:
            #     await account_user(message)
            # else:
            if collchats.count_documents({"user_chat_id": message.chat.id}) != 0:
                keyboard = ReplyKeyboardMarkup(
                    [[KeyboardButton("💔 Suhbatni yakunlash")]], resize_keyboard=True, one_time_keyboard=True)
                await message.answer("Siz hozirda kim bilandir suhbatlashyapsiz", reply_markup=keyboard)
            else:
                if collqueue.count_documents({"_id": message.chat.id}) != 1:
                    keyboard = ReplyKeyboardMarkup(
                        [[KeyboardButton("📛 Izlashni to'xtatish")]], resize_keyboard=True)
                    finder_acc = collusers.find_one({"_id": message.from_user.id})
                    if finder_acc.get("gender") != "👩‍ Ayol kishi":
                        interlocutor = collqueue.find_one({"_sex": {"$nin": ["👩‍ Ayol kishi"]}})
                        if interlocutor is None:
                            interlocutor = collqueue.find_one()
                    else:
                        interlocutor = collqueue.find_one({"reputation": True})
                        if interlocutor is None:
                            interlocutor = collqueue.find_one()
                    # queue_search = list(collqueue.aggregate([{"$sample": {"size": 1}}]))
                    # if queue_search:
                    #     if queue_search[0]["_id"] != message.chat.id:
                    #         interlocutor = queue_search[0]

                    # if interlocutor is None:
                    #     user_gender_var = finder_acc.get('gender')
                    #     user_find = finder_acc.get('finding')
                    #     if user_find == "👤 Muhim emas":
                    #         interlocutor = collqueue.find_one(
                    #             {
                    #                 "_sex": {
                    #                     "$in":
                    #                         ["👩‍ Ayol kishi",
                    #                          "👨‍ Yigit kishi"]
                    #                 },
                    #                 "_finding": {
                    #                     "$in":
                    #                         [finder_acc.get('gender'),
                    #                          "👤 Muhim emas"]
                    #                 }
                    #             })
                    #     elif user_gender_var == "👤 Muhim emas":
                    #         # TODO: clear after change
                    #         interlocutor = collqueue.find_one(
                    #             {
                    #                 "_sex": finder_acc.get('finding'),
                    #                 "$or":
                    #                     [
                    #                         {"_finding": "👤 Muhim emas"},
                    #                         {"_finding": "👩‍ Ayol kishi"},
                    #                         {"_finding": "👨‍ Yigit kishi"}
                    #                     ],
                    #             })
                    #     elif user_gender_var == "👤 Muhim emas" and user_find == "👤 Muhim emas":
                    #         interlocutor = collqueue.find_one({})
                    if interlocutor is None:
                        acc = collusers.find_one({"_id": message.from_user.id})
                        collqueue.insert_one({
                            "_id": message.chat.id,
                            "_sex": acc.get('gender'),
                            # "_finding": acc.get('finding')
                        })
                        await message.answer(
                            "🕒 Suhbatdoshni izlash boshlandi...", reply_markup=keyboard)
                    else:
                        if collqueue.count_documents({"_id": interlocutor["_id"]}) != 0:
                            collqueue.delete_one({"_id": message.chat.id})
                            collqueue.delete_one({"_id": interlocutor["_id"]})

                            collchats.insert_one(
                                {
                                    "user_chat_id": message.chat.id,
                                    "interlocutor_chat_id": interlocutor["_id"]
                                }
                            )
                            collchats.insert_one(
                                {
                                    "user_chat_id": interlocutor["_id"],
                                    "interlocutor_chat_id": message.chat.id
                                }
                            )
                            # nickname_intestlocutor = collusers.find_one(
                            #     {"_id": message.chat.id}).get("nickname", "Yo'q")
                            # bio_intestlocutor = collusers.find_one(
                            #     {"_id": message.chat.id}).get("bio", "Bio mavjud emas")
                            # gender_intestlocutor = collusers.find_one(
                            #     {"_id": message.chat.id}).get("gender", "Noaniq")
                            # bio_user = collusers.find_one({"_id": collchats.find_one(
                            #     {"user_chat_id": message.chat.id})["interlocutor_chat_id"]}).get("bio", "Bio yo'q")
                            # nickname_user = collusers.find_one({"_id": collchats.find_one(
                            #     {"user_chat_id": message.chat.id})["interlocutor_chat_id"]}).get("nickname", "Yo'q")
                            # gender_user = collusers.find_one({"_id": collchats.find_one(
                            #     {"user_chat_id": message.chat.id})["interlocutor_chat_id"]}).get("gender", "Noaniq")
                            keyboard_leave = ReplyKeyboardMarkup([[
                                KeyboardButton(
                                    "💔 Suhbatni yakunlash")]],
                                resize_keyboard=True, one_time_keyboard=True)
                            chat_info = collchats.find_one({"user_chat_id": message.chat.id})[
                                "interlocutor_chat_id"]
                            # TODO blocking users look bot-log-01-26.log
                            await message.answer(
                                "Suhbatdosh topildi!😉\n",
                                # "Suhbatni boshlashingiz mumkin.🥳\n"
                                # f"\nSuhbatdoshingiz tahallusi: {nickname_user}\n"
                                # f"Suhbatdoshingiz biosi: {bio_user}\n"
                                # f"Suhbatdoshingiz jinsi: {gender_user}",
                                reply_markup=keyboard_leave)
                            await bot.send_message(
                                text="Suhbatdosh topildi!😉\n",
                                # "Suhbatni boshlashingiz mumkin.🥳\n\n"
                                # f"Suhbatdosh tahallusi: {nickname_intestlocutor}\n"
                                # f"Suhbatdosh biosi: {bio_intestlocutor}\n"
                                # f"Suhbatdosh jinsi: {gender_intestlocutor}",
                                chat_id=chat_info,
                                reply_markup=keyboard_leave)
                        else:
                            collqueue.insert_one({"_id": message.chat.id})
                            logging.warning("Shu joyi qachondir ishlarmikin?!")
                            await message.answer(
                                "🕒 Suhbatdoshni izlash boshlandi...", reply_markup=keyboard)
                else:
                    keyboard = ReplyKeyboardMarkup(
                        [[KeyboardButton("📛 Izlashni to'xtatish")]], resize_keyboard=True)
                    await message.answer("Siz suhbatdosh izlayapsiz, biroz sabr qiling 🕒😉", reply_markup=keyboard)
    else:
        await following_channel(message)


async def search_girl_func():
    interlocutor = collqueue.find_one({"_sex": "👩‍ Ayol kishi"})
    return interlocutor


@dp.message_handler(commands=["search_girl", "searchgirl"])
async def search_girl_act(message: types.Message):
    user_follow_act = await admin_commands.is_authenticated(message)
    acc = collusers.find_one({"_id": message.from_user.id})
    if not acc:
        await account_registration_act(message)
    if user_follow_act and acc.get("balance", 0) > 9:
        if message.chat.type == "private":
            if collchats.count_documents({"user_chat_id": message.chat.id}) != 0:
                keyboard = ReplyKeyboardMarkup(
                    [[KeyboardButton("💔 Suhbatni yakunlash")]], resize_keyboard=True, one_time_keyboard=True)
                await message.answer("Siz hozirda kim bilandir suhbatlashyapsiz", reply_markup=keyboard)
            else:
                if collqueue.count_documents({"_id": message.chat.id}) != 1:
                    keyboard = ReplyKeyboardMarkup(
                        [[KeyboardButton("📛 Izlashni to'xtatish")]], resize_keyboard=True)
                    interlocutor = await search_girl_func()
                    await message.answer(
                        "🕒 Suhbatdoshni izlash boshlandi...", reply_markup=keyboard)
                    if interlocutor is None:
                        await asyncio.sleep(5)
                        await message.answer("Qaytadan urunib ko'ryapmiz...")
                        await asyncio.sleep(5)
                        await search_girl_func()
                        if interlocutor is None:
                            await message.answer("Hozirda bizda online Qizlar (Ayollar) mavjud emas\n"
                                                 "Bordiyu online bo'lsa sizga xabar beramiz",
                                                 reply_markup=keyboard)

                    if interlocutor is None:
                        collqueue.insert_one({
                            "_id": message.chat.id,
                            "reputation": True,
                            # "_finding": acc.get('finding')
                        })
                    else:
                        if collqueue.count_documents({"_id": interlocutor["_id"]}) != 0:
                            collqueue.delete_one({"_id": message.chat.id})
                            collqueue.delete_one({"_id": interlocutor["_id"]})

                            collchats.insert_one(
                                {
                                    "user_chat_id": message.chat.id,
                                    "interlocutor_chat_id": interlocutor["_id"]
                                }
                            )
                            collchats.insert_one(
                                {
                                    "user_chat_id": interlocutor["_id"],
                                    "interlocutor_chat_id": message.chat.id
                                }
                            )
                            keyboard_leave = ReplyKeyboardMarkup([[
                                KeyboardButton(
                                    "💔 Suhbatni yakunlash")]],
                                resize_keyboard=True, one_time_keyboard=True)
                            chat_info = collchats.find_one({"user_chat_id": message.chat.id})[
                                "interlocutor_chat_id"]

                            await message.answer(
                                "Suhbatdosh topildi!😉\n",
                                reply_markup=keyboard_leave)
                            await bot.send_message(
                                text="Suhbatdosh topildi!😉\n",
                                chat_id=chat_info,
                                reply_markup=keyboard_leave)
                        else:
                            collqueue.insert_one({"_id": message.chat.id})
                            logging.warning("Shu joyi qachondir ishlarmikin?!")
                            await message.answer(
                                "🕒 Suhbatdoshni izlash boshlandi...", reply_markup=keyboard)
                else:
                    keyboard = ReplyKeyboardMarkup(
                        [[KeyboardButton("📛 Izlashni to'xtatish")]], resize_keyboard=True)
                    await message.answer("Siz suhbatdosh izlayapsiz, biroz sabr qiling 🕒😉", reply_markup=keyboard)
    else:
        await reposting_bot(message)


@dp.message_handler(commands=["stop_search"])
async def stop_search_act(message: types.Message):
    if collqueue.count_documents({"_id": message.chat.id}) != 0:
        collqueue.delete_one({"_id": message.chat.id})
        await menu(message)
    else:
        await message.answer("Siz suhbatdosh izlamayapsiz")
        await menu(message)


@dp.message_handler(commands=["ha"])
async def yes_rep_act(message: types.Message):
    if collchats.count_documents({"user_chat_id": message.chat.id}) != 0:
        collusers.update_one({"_id": collchats.find_one({"user_chat_id": message.chat.id})[
            "interlocutor_chat_id"]}, {"$inc": {"reputation": 5}})
        collchats.delete_one({"user_chat_id": message.chat.id})
        collchats.update_many({"interlocutor_chat_id": message.chat.id}, {"$set": {"status": False}})
        keyboard = config.main_menu_keyboard
        await message.answer("Javobingiz uchun rahmat!☺️", reply_markup=keyboard)
    else:
        await message.answer("Siz suhbatdosh bilan yozishmayapsiz")
        await menu(message)


@dp.message_handler(commands=["yoq"])
async def no_rep_act(message: types.Message):
    if collchats.count_documents({"user_chat_id": message.chat.id}) != 0:
        collusers.update_one({"_id": collchats.find_one({"user_chat_id": message.chat.id})[
            "interlocutor_chat_id"]}, {"$inc": {"reputation": -5}})
        collchats.delete_one({"user_chat_id": message.chat.id})
        collchats.update_many({"interlocutor_chat_id": message.chat.id}, {"$set": {"status": False}})
        keyboard = config.main_menu_keyboard
        await message.answer("Javobingiz uchun rahmat!☺️", reply_markup=keyboard)
    else:
        await message.answer("Siz suhbatdosh bilan yozishmayapsiz")
        await menu(message)


@dp.message_handler(commands=["report_user"])
async def report_rep_act(message: types.Message):
    if collchats.count_documents({"user_chat_id": message.chat.id}) != 0:
        rep_user_id = collchats.find_one({"user_chat_id": message.chat.id})["interlocutor_chat_id"]
        collusers.update_one({"_id": rep_user_id}, {"$inc": {"reputation": -25}})
        collbans.insert_one({"id": rep_user_id,
                             "time": int(message.date.timestamp())})
        collchats.delete_one({"user_chat_id": message.chat.id})
        collchats.update_many({"interlocutor_chat_id": message.chat.id}, {"$set": {"status": False}})
        keyboard = config.main_menu_keyboard
        await message.answer("Shikoyatingiz qabul qilindi!☺️", reply_markup=keyboard)
    else:
        await message.answer("Siz suhbatdosh bilan yozishmayapsiz")
        await menu(message)


@dp.message_handler(commands=['stat'])
async def mini_stats_info(message: types.Message):
    users = cluster.chatbot.command('collstats', 'users')
    queue_stats = cluster.chatbot.command('collstats', 'queue')
    chats = cluster.chatbot.command('collstats', 'chats')
    msg = "Statistika:\n" \
          f"Users: {users.get('count', '0')}\n" \
          f"Chats: {chats.get('count', '0')}\n" \
          f"Queue's: {queue_stats.get('count', '0')}"
    await message.answer(msg)


@dp.message_handler(commands=['delete_chats'])
async def delete_chats(message: types.Message):
    await admin_commands.delete_blocked_chats(message)


@dp.message_handler(commands=['admin'])
async def admin_help_message(message: types.Message):
    if message.from_user.id in config.admin_ids:
        await message.answer("Hozirda mavjud admin komandalar\n"
                             "/admin - Ushbu xabarni chaqirish\n"
                             "/stat - Qisqacha statistika\n"
                             "/all_stats - to'liq statistika\n"
                             "/post - Foydalanuvchilarga xabarnoma jo'natish")
    else:
        await message.answer("Bunday buyruq botda mavjud emas!")


@dp.message_handler(commands=['all_stats'])
async def all_stats_info(message: types.Message):
    user_stats = await admin_commands.user_statistics()
    chat_all_list, chat_block_list = await admin_commands.chat_statistics()
    queue_stats = await admin_commands.queue_statistics()
    msg = "Barcha statistika:\n\n" \
          f"     *Users*   \n{user_stats}\n\n" \
          f"     *Chats* \nAll:{len(chat_all_list) - len(chat_block_list)}\n" \
          f"     *Queue's*  \n{queue_stats}"
    await message.answer(msg, parse_mode="MarkdownV2")


@dp.message_handler(commands=["yakunlash", "leave", "leave_chat"])
async def leave_from_chat_act(message: types.Message):
    if collchats.count_documents({"user_chat_id": message.chat.id}) != 0:
        await message.answer("Siz chatni tark etdingiz")
        keyboard = ReplyKeyboardMarkup(
            [
                [
                    KeyboardButton("👍 Ha"),
                    KeyboardButton("👎 Yo'q")
                ],
                [
                    KeyboardButton("🗣 Shikoyat berish")
                ]
            ],
            resize_keyboard=True
        )
        try:
            await bot.send_message(text="Suhbatdoshingiz chatni tark etdi,\n"
                                        "Muloqot maroqli o'tdimi?",
                                   chat_id=collchats.find_one(
                                       {"user_chat_id": message.chat.id}).get("interlocutor_chat_id"),
                                   reply_markup=keyboard)
            await bot.send_message(text="Suhbatdosh bilan muloqot maroqli o'tdimi?",
                                   chat_id=collchats.find_one(
                                       {"user_chat_id": message.chat.id}).get("user_chat_id"),
                                   reply_markup=keyboard)
        except Exception as e:
            collchats.delete_one({"user_chat_id": message.chat.id})
            await menu(message)
            logging.error(f"Ushbu foydalanuvchida xato yuz berdi: {e}")

    else:
        await message.answer("Siz suhbatdosh bilan yozishmayapsiz")
        await menu(message)


@dp.message_handler(commands=["report"])
async def taklif_user_message(message):
    x = await SetReport.report.set()
    await message.answer("Bizga o'z takliflaringizni yuboring!")


@dp.message_handler(commands=["follow"])
@dp.throttled(rate=1)
async def following_channel(msg):
    try:
        keyboard_buttons = []
        for i in config.channel_urls_dict:
            keyboard_buttons.append(
                InlineKeyboardButton(f"{i.get('title')}",
                                     url=i.get('link')))
        inline_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                keyboard_buttons,
                [InlineKeyboardButton("✅ Tasdiqlash",
                                      callback_data=CallbackData("choice", "action").new(
                                          action="channel_subscribe"))]
            ],
            one_time_keyboard=True
        )
        await msg.answer("Kanalga a'zo bo'lish majburiy!", reply_markup=inline_keyboard)
    except Exception as e:
        logging.error(f"XATOLIK YUZ BERDI: {e}")


@dp.message_handler(commands=["repost"])
async def reposting_bot(msg):
    try:
        acc = collusers.find_one({"_id": msg.from_user.id})
        balance = acc.get('balance', 0)
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Do'st topish", url=f"https://t.me/davra_bot?start={msg.from_user.id}"))
        await msg.answer("To'g'ridan-to'g'ri qizlar izlash funksiyasini yoqish uchun *10* "
                         "nafar *yangi* foydalanuvchi havola orqali botga a'zo qilishingiz talab qilinadi\n\n"
                         "Hozirda siz qo'shgan *yangi* foydalanuvchilar soni:\n"
                         f"👤: *{balance}*\n\n",
                         parse_mode="markdown")
        await msg.answer("Do'stlar orttirishni hoxlaysizmi?\n"
                         "Unda shu havolani ulashing:\n\n"
                         f"`t.me/davra_bot?start={msg.from_user.id}`\n\n"
                         f"[Do'st orttirish uchun havola](t.me/davra_bot?start={msg.from_user.id}\n",
                         reply_markup=keyboard, parse_mode="markdown")
    except Exception as e:
        logging.error(f"XATOLIK YUZ BERDI: {e}")


@dp.message_handler(state=SetReport.report, content_types=["text", "sticker", "photo", "voice", "document", "video"])
async def taklif_process(message: types.Message, state: FSMContext):
    if message.text == "✅ Tasdiqlash":
        await message.answer("Yuborildi!")
        await state.finish()
        await menu(message)
    elif message.text == "🏠 Bosh menyu":
        await state.finish()
        await menu(message)
    elif message.text == "☕️ Tasodifiy suhbatdosh":
        await state.finish()
        await search_user_act(message)
    elif message.text == "👩 Qizlar izlash":
        await state.finish()
        await search_girl_act(message)
    elif message.text == "🗣 Takliflar":
        await state.finish()
        await taklif_user_message(message)
    else:
        if message.voice:
            await bot.send_voice(chat_id=config.group_id, voice=message.voice.file_id,
                                 caption=message.caption, caption_entities=message.caption_entities)
        elif message.video:
            await bot.send_video(chat_id=config.group_id, video=message.video,
                                 caption=message.caption)
        elif message.photo:
            await bot.send_photo(chat_id=config.group_id, photo=message.photo[-1].file_id,
                                 caption=message.caption)
        elif message.sticker:
            await bot.send_sticker(chat_id=config.group_id, sticker=message.sticker.file_id)
        elif message.text:
            await bot.send_message(chat_id=config.group_id, text=f"UserID:{message.from_user.id}\n"
                                                                 f"{message.text}")
        elif message.document:
            await bot.send_document(chat_id=config.group_id, document=message.document.file_id)
        # await state.finish()
        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("✅ Tasdiqlash"), KeyboardButton("🏠 Bosh menyu")
              ]], resize_keyboard=True, one_time_keyboard=True)
        await message.answer("Yuborish kerakmi?", reply_markup=keyboard)


@dp.message_handler(content_types=["text", "sticker", "photo", "voice", "document", "video", "video_note", "animation"])
@dp.edited_message_handler()
@dp.throttled(on_throttled=handler_throttled, rate=1)
async def some_text(message: types.Message):
    if message.text == "💔 Suhbatni yakunlash":
        return await leave_from_chat_act(message)

    elif message.text == "👍 Ha":
        return await yes_rep_act(message)
    elif message.text == "👎 Yo'q":
        return await no_rep_act(message)
    elif message.text == "🗣 Shikoyat berish":
        return await report_rep_act(message)
    elif message.text == "📛 Izlashni to'xtatish":
        return await stop_search_act(message)
    elif message.text == "ℹ️ Qo'llanma":
        return await message.answer("[Ushbu maqola qisqacha bot haqida tushuncha berib o'tilgan]"
                                    "(https://telegra.ph/Davra-uz--Yoriqnoma-03-05)", parse_mode="Markdown")
    elif message.text == "🗣 Takliflar":
        return await message.answer("Ushbu buyruq hozirda mavjud emas\n"
                                    "/start ni bosing")
    elif message.text == "📝 Ro'yxatdan o'tish":
        return await account_registration_act(message)
    elif message.text == "🗣 Do'stlarga ulashish":
        return await referal_link(message)
    elif message.text == "✏ Jins":
        return await user_gender(message)
    elif message.text == "✏ Kim bilan suxbatlashish?":
        return await user_finding(message)
    elif message.text == "✏ Tahallusni o'zgartirish":
        return await user_tahallus(message)
    elif message.text == "✏ Bio":
        return await user_bio(message)
    elif message.text == "✏ Haqimda":
        return await user_bio_change(message)
    elif message.text == "🖼 Suratni alishtirish":
        return await user_photo(message)
    elif message.text == "🚫 Bekor qilish" or message.text == "✖️Bekor qilish":
        return await menu(message)
    if collbans.count_documents({"id": message.from_user.id}) < 4:
        chat = collchats.find_one({"user_chat_id": message.chat.id})
        # if message.photo:
        #     await message.answer(message.photo[-1].file_id)
        if message.text == "☕ Anketalardan izlash":
            return await search_anketa(message)
        elif message.text == "🏠 Bosh menyu":
            return await menu(message)
        # elif message.text == "💣 Anketani o'chirish":
        #     await remove_account_act(message)
        elif message.text == "☕️ Tasodifiy suhbatdosh":
            return await search_user_act(message)
        elif message.text == "🔖 Anketa":
            return await account_user(message)
        elif message.text == "🏠 Bosh menyu":
            return await menu(message)
        elif chat:
            if message.content_type == "text":
                try:
                    await bot.send_message(
                        chat_id=collchats.find_one({"user_chat_id": message.chat.id})["interlocutor_chat_id"],
                        text=message.text, entities=message.entities)
                except (BotKicked, BotBlocked, UserDeactivated):
                    await admin_commands.user_are_blocked_bot(message)
            elif chat.get("status", True):
                if message.content_type == "sticker":
                    try:
                        await bot.send_sticker(
                            chat_id=collchats.find_one({"user_chat_id": message.chat.id})["interlocutor_chat_id"],
                            sticker=message.sticker["file_id"])
                    except (BotKicked, BotBlocked, UserDeactivated):
                        await admin_commands.user_are_blocked_bot(message)
                elif message.content_type == "photo":
                    try:
                        await bot.send_photo(
                            chat_id=collchats.find_one({"user_chat_id": message.chat.id})["interlocutor_chat_id"],
                            photo=message.photo[len(message.photo) - 1].file_id)
                    except (BotKicked, BotBlocked, UserDeactivated):
                        await admin_commands.user_are_blocked_bot(message)
                elif message.content_type == "voice":
                    try:
                        await bot.send_voice(
                            chat_id=collchats.find_one({"user_chat_id": message.chat.id})["interlocutor_chat_id"],
                            voice=message.voice["file_id"])
                    except (BotKicked, BotBlocked, UserDeactivated):
                        await admin_commands.user_are_blocked_bot(message)
                elif message.content_type == "document":
                    try:
                        await bot.send_document(
                            chat_id=collchats.find_one({"user_chat_id": message.chat.id})["interlocutor_chat_id"],
                            document=message.document["file_id"])
                    except (BotKicked, BotBlocked, UserDeactivated):
                        await admin_commands.user_are_blocked_bot(message)
                elif message.content_type == "video":
                    try:
                        await bot.send_video(
                            chat_id=collchats.find_one({"user_chat_id": message.chat.id})["interlocutor_chat_id"],
                            video=message.video["file_id"])
                    except (BotKicked, BotBlocked, UserDeactivated):
                        await admin_commands.user_are_blocked_bot(message)
                elif message.content_type == "video_note":
                    try:
                        await bot.send_video_note(
                            chat_id=collchats.find_one({"user_chat_id": message.chat.id})["interlocutor_chat_id"],
                            video_note=message.video_note["file_id"])
                    except (BotKicked, BotBlocked, UserDeactivated):
                        await admin_commands.user_are_blocked_bot(message)
                elif message.content_type == "animation":
                    try:
                        await bot.send_animation(
                            chat_id=collchats.find_one({"user_chat_id": message.chat.id})["interlocutor_chat_id"],
                            animation=message.document["file_id"])
                    except (BotKicked, BotBlocked, UserDeactivated):
                        await admin_commands.user_are_blocked_bot(message)
            else:
                keyboard = ReplyKeyboardMarkup(
                    [[KeyboardButton("👍 Ha"), KeyboardButton("👎 Yo'q")],
                     [KeyboardButton("🗣 Shikoyat berish")]], resize_keyboard=True)
                await message.answer("Suhbatdoshingiz chatni tark etgan! Spam qilmang!", reply_markup=keyboard)
    else:
        ban_time = collbans.find_one({"id": message.from_user.id}, sort=[('time', -1)])['time']
        current_time = message.date.timestamp()
        time_has_passed_seconds = current_time - ban_time
        active_time = ban_time + config.ban_seconds + 18000   # UTC +5
        if time_has_passed_seconds < config.ban_seconds:
            await message.answer("*Ma'muriyat:*\n"
                                 "Siz juda ko'p shikoyat olganingiz uchun botdan biroz muddat foydalana olmaysiz\n\n"
                                 f"Faol bo'lish vaqti: *{datetime.datetime.fromtimestamp(active_time)}*",
                                 parse_mode="Markdown")
        else:
            await asyncio.sleep(1)
            await message.answer("Blokdan chiqish jarayoni... ⏳")
            await asyncio.sleep(2)
            collbans.delete_many({"id": message.from_user.id})
            await asyncio.sleep(2)
            await message.answer("Siz muvaffaqiyatli blokdan chiqdingiz!\n"
                                 "Iltimos qoidalarni buzmang😉")


@dp.callback_query_handler(text_contains="remove")
async def process_remove_account(callback: types.CallbackQuery):
    await callback.answer()
    try:
        collusers.delete_one({"_id": callback.from_user.id})
        await callback.message.answer("Siz muvaffaqiyatli anketangizni o'chirdingiz")
        await menu(callback.message)
    except Exception as e:
        logging.error(f"XATOLIK YUZ BERDI: {e}")


@dp.callback_query_handler(text_contains="cancel")
async def process_cancel(callback: types.CallbackQuery):
    await callback.answer()
    try:
        await callback.message.answer("Yaxshi, qaytib bunaqa hazil qilmang 😉")
    except Exception as e:
        logging.error(f"XATOLIK YUZ BERDI: {e}")


@dp.callback_query_handler(text_contains='channel_subscribe')
async def channel_affirmative_reg(callback_query: types.CallbackQuery):
    await callback_query.answer()
    try:
        if await admin_commands.is_authenticated(callback_query):
            await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
            await menu(callback_query)
        else:
            await callback_query.answer(text="A'zo bo'lmadingiz!", show_alert=True)
    except Exception as e:
        logging.error(f"CHANNEL SUBSCRIBE XATO: {e}")


@dp.callback_query_handler(config.liked_cb.filter(action=["liked"]))
@dp.throttled(on_throttled=handler_throttled, rate=1)
async def liked_callback(callback: types.CallbackQuery):
    try:
        await callback.answer("Ovoz bergansiz")
    except Exception as e:
        logging.error(f"XATOLIK YUZ BERDI: {e}")


@dp.callback_query_handler(config.vote_cb.filter(action=['yes', 'no']))
async def yes_callback(callback: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    try:
        await dp.throttle('vote', rate=2)
    except Throttled:
        return await callback.answer('Sabr qil')
    await callback.answer()
    # sending callback reaction and answer user
    try: # noqa
        await send_reaction_func(sender_id=callback.from_user.id, callback_data=callback_data)
        # change reply keyboard and change callback data from keyboard
        old_keyboard = await config.like_keyboard(user_id=callback.from_user.id)
        await callback.message.edit_reply_markup(reply_markup=old_keyboard)
        # sending new anketa
        text, photo, tg_id = await send_new_anketa(callback.from_user.id)
        if tg_id:
            new_keyboard = await config.like_keyboard(new=True, user_id=tg_id)
            await callback.message.answer_photo(photo=photo, caption=text, reply_markup=new_keyboard)
        else:
            await callback.message.answer_photo(photo=photo, caption=text)
    except Exception as e:
        logging.error(f"XATOLIK YUZ BERDI: {e}")


@dp.callback_query_handler(config.confirm_cb.filter(action=['confirm']))
@dp.throttled(on_throttled=handler_throttled, rate=1)
async def confirm_callback(callback: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    # confirming and refusing callback reaction and answer user
    try:
        await dp.throttle('confirm', rate=4)
    except Throttled:
        return await callback.answer('Sabr qil')
    await callback.answer("Qabul qilindi")
    try:
        # action = callback_data['action']
        tg_id = callback_data['id']
        # insert db prqueue query
        await insert_db_prque(callback.from_user.id, tg_id, True)
        # insert db prchat query
        await confirm_pr_chat_users(int(tg_id), callback.from_user.id)
        # sending new message
        mail_keyboard = await config.send_mail_keyboard(tg_id)
        another_user_mail_keyboard = await config.send_mail_keyboard(str(callback.from_user.id))
        await callback.message.answer("Siz muvaffaqiyatli qabul qildingiz\nXat yozasizmi?", reply_markup=mail_keyboard)
        # sending confirmation text from another user
        acc = collusers.find_one({"_id": callback.from_user.id})
        photo = acc.get("photo", None)
        if not photo:
            photo = DEFAULT_WOMAN_PHOTO if acc.get("gender", None) == "👩‍ Ayol kishi" else DEFAULT_MAN_PHOTO
        text = "*Ushbu foydlanuvchi sizni qabul qildi*\n" \
               "Foydalanuvchi: {}\n" \
               "Bio: {}\n" \
               "Jins: {}\n" \
               "*Javob berasizmi?*".format(acc.get("nickname", "Noma'lum"), acc.get("bio"),
                                           acc.get("gender", "Ma'lum emas"))
        await bot.send_photo(int(tg_id), photo, caption=text, parse_mode="Markdown",
                             reply_markup=another_user_mail_keyboard)
        old_keyboard = await config.like_keyboard(user_id=callback.from_user.id)
        await callback.message.edit_reply_markup(reply_markup=old_keyboard)
    except Exception as e:
        logging.error(f"XATOLIK YUZ BERDI: {e}")


@dp.callback_query_handler(config.confirm_cb.filter(action=['refuse']))
@dp.throttled(on_throttled=handler_throttled, rate=1)
async def confirm_callback(callback: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    try:
        await dp.throttle('confirm', rate=4)
    except Throttled:
        return await callback.answer('Sabr qil')
    await callback.answer("Bekor qilindi")
    try:
        # confirming and refusing callback reaction and answer user
        # action = callback_data['action']
        tg_id = callback_data['id']
        await insert_db_prque(callback.from_user.id, tg_id)
        old_keyboard = await config.like_keyboard(user_id=callback.from_user.id)
        await callback.message.edit_reply_markup(reply_markup=old_keyboard)
    except Exception as e:
        logging.error(f"XATOLIK YUZ BERDI: {e}")


@dp.callback_query_handler(config.mail_cb.filter(action=['mail']))
async def mail_callback(callback: types.CallbackQuery, state: FSMContext, callback_data: typing.Dict[str, str]):
    try:
        await dp.throttle('mail', rate=4)
    except Throttled:
        return await callback.answer('Sabr qil')
    await callback.answer()
    try:
        # action = callback_data['action']
        tg_id = callback_data['id']
        # await callback.answer("Menga xabar yozing")
        await Anketa.user_id.set()
        async with state.proxy() as data:
            data["user_id"] = tg_id
        await callback.message.answer("O'z xatingizni yozing",
                                      reply_markup=await config.send_mail_keyboard(tg_id, cancel=True))
        # TODO: NEED REALIZE PRCHATS LIST
    except Exception as e:
        logging.error(f"XATOLIK YUZ BERDI: {e}")


@dp.message_handler(state=Anketa.user_id, content_types=["text", "sticker", "photo",
                                                         "voice", "document", "videoThrottled!", "video_note"])
async def get_message(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            if data:
                if message.text == "🚫 Bekor qilish":
                    await message.answer("Bekor qilindi")
                    await menu(message)
                    return await state.finish()
                user = collusers.find_one({"_id": message.from_user.id})
                await send_message_for_tg_id(message, int(data['user_id']), anketa=True, nickname=user.get('nickname'))
                await message.answer("Xatingiz yuborildi!")
                await menu(message)
                await state.finish()
            else:
                await state.finish()
    except Exception as e:
        logging.error(f"XATOLIK YUZ BERDI: {e}")


# @dp.callback_query_handler(state=Anketa.user_id)
# async def any_callback(callback: types.CallbackQuery, state):
#     action, tg_id = callback.data.split(":") # noqa
#     if action == "mail":
#         async with state.proxy() as data:
#             data["user_id"] = tg_id
#             data["message"] = callback.message
#         await Anketa.user_id.set()
#     else:
#         pass
#         await callback.answer("Bekor qilindi!")
#     await callback.message.edit_text("O'z xatingizni yozing")


@dp.callback_query_handler()
@dp.throttled(on_throttled=handler_throttled, rate=4)
async def any_callback_answer(callback: types.CallbackQuery):
    await callback.answer("Biroz kuting")


@dp.message_handler()
@dp.throttled(on_throttled=handler_throttled, rate=4)
async def any_message_answer(message: types.Message):
    await message.answer("Biroz kuting")


@dp.errors_handler(exception=MessageNotModified)
async def message_not_modified_handler(update, error):
    logging.error(f"MESSAGE NOT MODIFIED: {update}\n{error}")
    return True # errors_handler must return True if error was handled correctly


if __name__ == "__main__":
    print("Bot ishga tushirilmoqda...")
    executor.start_polling(dp)
