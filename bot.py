import logging

from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import BotBlocked, BotKicked, UserDeactivated
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from pymongo import MongoClient
import admin_commands
import config

from config import BOT_TOKEN, MONGO_URL

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

cluster = MongoClient(MONGO_URL)
collqueue = cluster.chatbot.queue
collusers = cluster.chatbot.users
collchats = cluster.chatbot.chats
collrefs = cluster.chatbot.refs


class SetBio(StatesGroup):
    finding = State()
    user_bio = State()
    gender = State()
    nickname = State()


class SetRegBio(StatesGroup):
    finding = State()
    user_bio = State()
    gender = State()
    referal = State()


class SetPost(StatesGroup):
    post = State()
    inactive_post = State()


class SetReport(StatesGroup):
    report = State()


@dp.message_handler(commands="main_menu")
async def menu(message: types.Message or types.CallbackQuery):
    keyboard = ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("☕️ Suhbatdosh izlash")
            ],
            [
                # KeyboardButton("🔖 Anketa")
                KeyboardButton("🗣 Takliflar")
            ]
        ],
        resize_keyboard=True
    )
    await bot.send_message(chat_id=message.from_user.id, text="🏠 Bosh menyu", reply_markup=keyboard)


@dp.message_handler(commands="start")
async def start_menu(message: types.Message):
    if collusers.count_documents({"_id": message.from_user.id}) == 0:
        # Adding new user DB
        collusers.insert_one({"_id": message.from_user.id})
    elif collusers.count_documents({"_id": message.from_user.id, "status": False}) == 1:
        collusers.update_one({"_id": message.from_user.id}, {"$set": {"status": True}})
    else:
        collusers.update_one({"_id": message.from_user.id}, {"$set": {"status": True}})
    if len(message.text.split()) == 2 and message.from_user.id != int(message.text.split()[1]) and \
            collrefs.count_documents({"_ref": int(message.text.split()[1])}) == 0:
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

    keyboard = ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("☕️ Suhbatdosh izlash")
            ],
            [
                # KeyboardButton("🔖 Anketa")
                KeyboardButton("🗣 Takliflar")
            ]
        ],
        resize_keyboard=True
    )

    await message.answer("🏠 Bosh menyu", reply_markup=keyboard)


@dp.message_handler(commands=["anketa", "set_bio", "new_bio", "about_me"])
async def user_bio(message: types.Message):
    if collusers.count_documents({"_id": message.from_user.id}) == 0:
        await account_user(message)
    else:
        keyboard = ReplyKeyboardMarkup(
            [
                [
                    KeyboardButton("✏ Haqimda"),
                    KeyboardButton("✏ Jins")
                ],
                [
                    KeyboardButton("✏ Kim bilan suxbatlashish?"),
                ],
                [
                    KeyboardButton("✏ Tahallusni o'zgartirish"),
                ],
                [
                    KeyboardButton("🔖 Anketa"),
                ]
            ],
            resize_keyboard=True
        )
        await message.answer("Qaysi bo'limni o'zgartirishni istaysiz?", reply_markup=keyboard)


@dp.message_handler(commands=["haqimda", "me_bio"])
async def user_bio_change(message: types.Message):
    if collusers.count_documents({"_id": message.from_user.id}) == 0:
        await account_user(message)
    else:
        await SetBio.user_bio.set()
        await message.answer("Iltimos, qisqacha o'zingiz haqingizda yozing")


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
              KeyboardButton("👤 Muhim emas")
              ]], resize_keyboard=True, one_time_keyboard=True)
        await message.answer("Iltimos, kimlar bilan suhbat qurishingizni tanlang", reply_markup=keyboard)


@dp.message_handler(commands=["tahallus", "set_nickname", "new_nickname", "about_nickname"])
async def user_tahallus(message: types.Message):
    if collusers.count_documents({"_id": message.from_user.id}) == 0:
        await account_user(message)
    else:
        await SetBio.nickname.set()
        await message.answer("Iltimos, o'z tahallusingizni yozing")


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
        data["user_bio"] = message.text
        collusers.update_one({"_id": message.from_user.id}, {
            "$set": {"bio": data["user_bio"]}})

        await message.answer("Ma'lumotlar saqlandi")
        await state.finish()
    await menu(message)


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
               f"💵 Balans: {acc.get('balance', None)}\n" \
               f"⭐️Reyting: {acc.get('reputation', None)}\n" \
               f"📝Bio: {acc.get('bio', None)}\n" \
               f"👫Jins: {acc.get('gender', 'Noaniq')}\n" \
               f"👫Qidiruv: {acc.get('finding', 'Noaniq')}"
        keyboard = ReplyKeyboardMarkup(
            [
                [
                    KeyboardButton("☕️ Suhbatdosh izlash")
                ],
                [
                    KeyboardButton("💣 Anketani o'chirish"),
                    KeyboardButton("✏ Bio"),
                ],
                [
                    KeyboardButton("🗣 Do'stlarga ulashish")
                ],
                [
                    KeyboardButton("🏠 Bosh menyu"),
                ]
            ],
            resize_keyboard=True
        )

        await message.answer(text, reply_markup=keyboard)


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
        await SetRegBio.user_bio.set()
        await message.answer(f"Salom, {message.from_user.username}\nO'zingiz haqingizda yozing")
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
        await admin_commands.send_post_all_users(data, users)
        await state.finish()
        await menu(message)
    elif message.text == "✖️Bekor qilish":
        await state.finish()
        await menu(message)
    elif message.text == "☑️Faol emaslarga":
        data = await state.get_data()
        users = await admin_commands.get_all_inactive_users()
        await admin_commands.send_post_all_users(data, users)
        await state.finish()
        await menu(message)
    else:
        async with state.proxy() as data:
            if message.voice:
                data['type'] = 'voice'
                data['voice'] = message.voice.file_id
                data['caption'] = message.caption
                data['caption_entities'] = message.caption_entities
                await bot.send_voice(chat_id=message.from_user.id, voice=message.voice.file_id,
                                     caption=message.caption, caption_entities=message.caption_entities)
            elif message.video:
                data['type'] = 'video'
                data['video'] = message.video
                data['caption'] = message.caption
                data['caption_entities'] = message.caption_entities
                await bot.send_video(chat_id=message.from_user.id, video=message.video,
                                     caption=message.caption)
            elif message.photo:
                data['type'] = 'photo'
                data['photo'] = message.photo[-1].file_id
                data['caption'] = message.caption
                data['caption_entities'] = message.caption_entities
                await bot.send_photo(chat_id=message.from_user.id, photo=message.photo[-1].file_id,
                                     caption=message.caption)
            elif message.sticker:
                data['type'] = 'sticker'
                data['sticker'] = message.sticker.file_id
                await bot.send_sticker(chat_id=message.from_user.id, sticker=message.sticker.file_id)
            elif message.text:
                data['type'] = 'text'
                data['text'] = message.text
                data['entities'] = message.entities
                await bot.send_message(chat_id=message.from_user.id, text=message.text)
            elif message.document:
                data['type'] = 'document'
                data['document'] = message.document.file_id
                data['caption'] = message.caption
                data['caption_entities'] = message.caption_entities
                await bot.send_document(chat_id=message.from_user.id, document=message.document.file_id)
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

        await message.answer("Ma'lumotlar saqlandi")
        # await state.finish()
        await SetRegBio.gender.set()
        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("👨‍ Yigit kishi"),
              KeyboardButton("👩‍ Ayol kishi"),
              ]], resize_keyboard=True, one_time_keyboard=True)
        await message.answer("Iltimos, jinsingizni tanlang", reply_markup=keyboard)


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

        await message.answer("Ma'lumotlar saqlandi")
        # await state.finish()
        await SetRegBio.finding.set()
        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("👨‍ Yigit kishi"),
              KeyboardButton("👩‍ Ayol kishi"),
              KeyboardButton("👤 Muhim emas")
              ]], resize_keyboard=True, one_time_keyboard=True)
        await message.answer("Iltimos, kimlar bilan suhbat qurishingizni tanlang", reply_markup=keyboard)


@dp.message_handler(state=SetRegBio.finding)
async def process_set_finding_reg(message: types.Message, state: FSMContext):
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
                    # finder_acc = collusers.find_one({"_id": message.from_user.id})
                    # interlocutor = collqueue.find_one({"_sex": finder_acc.get('finding'),
                    #                                    "_finding": finder_acc.get('gender')})
                    interlocutor = None
                    queue_search = list(collqueue.aggregate([{"$sample": {"size": 1}}]))
                    if queue_search:
                        if queue_search[0]["_id"] != message.chat.id:
                            interlocutor = queue_search[0]

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
                        # acc = collusers.find_one({"_id": message.from_user.id})
                        collqueue.insert_one({
                            "_id": message.chat.id,
                            # "_sex": acc.get('gender'),
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
        keyboard = ReplyKeyboardMarkup(
            [
                [KeyboardButton("☕️ Suhbatdosh izlash")],
                # [KeyboardButton("🔖 Anketa")]
                [KeyboardButton("🗣 Takliflar")]
            ],
            resize_keyboard=True
        )
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
        keyboard = ReplyKeyboardMarkup(
            [
                [KeyboardButton("☕️ Suhbatdosh izlash")],
                # [KeyboardButton("🔖 Anketa")]
                [KeyboardButton("🗣 Takliflar")]
            ],
            resize_keyboard=True
        )
        await message.answer("Javobingiz uchun rahmat!☺️", reply_markup=keyboard)
    else:
        await message.answer("Siz suhbatdosh bilan yozishmayapsiz")
        await menu(message)


@dp.message_handler(commands=["report_user"])
async def report_rep_act(message: types.Message):
    if collchats.count_documents({"user_chat_id": message.chat.id}) != 0:
        collusers.update_one({"_id": collchats.find_one({"user_chat_id": message.chat.id})[
            "interlocutor_chat_id"]}, {"$inc": {"reputation": -25}})
        collchats.delete_one({"user_chat_id": message.chat.id})
        collchats.update_many({"interlocutor_chat_id": message.chat.id}, {"$set": {"status": False}})
        keyboard = ReplyKeyboardMarkup(
            [
                [KeyboardButton("☕️ Suhbatdosh izlash")],
                # [KeyboardButton("🔖 Anketa")]
                [KeyboardButton("🗣 Takliflar")]
            ],
            resize_keyboard=True
        )
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
async def all_stats_info(message: types.Message):
    await admin_commands.delete_blocked_chats(message)


@dp.message_handler(commands=['all_stats'])
async def all_stats_info(message: types.Message):
    user_stats = await admin_commands.user_statistics()
    chat_all_list, chat_block_list = await admin_commands.chat_statistics()
    queue_stats = await admin_commands.queue_statistics()
    msg = "Barcha statistika:\n\n" \
          f"     *Users*   \n{user_stats}\n\n" \
          f"     *Chats* \nAll:{len(chat_all_list)}\n" \
          f"     Blocked: {len(chat_block_list)}\n\n" \
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
    await SetReport.report.set()
    await message.answer("Bizga o'z takliflaringizni yuboring!")


@dp.message_handler(state=SetReport.report, content_types=["text", "sticker", "photo", "voice", "document", "video"])
async def taklif_process(message: types.Message, state: FSMContext):
    if message.text == "✅ Tasdiqlash":
        await message.answer("Yuborildi!")
        await state.finish()
        await menu(message)
    elif message.text == "🏠 Bosh menyu":
        await state.finish()
        await menu(message)
    elif message.text == "☕️ Suhbatdosh izlash":
        await state.finish()
        await search_user_act(message)
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
            await bot.send_message(chat_id=config.group_id, text=message.text)
        elif message.document:
            await bot.send_document(chat_id=config.group_id, document=message.document.file_id)
        # await state.finish()
        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("✅ Tasdiqlash"), KeyboardButton("🏠 Bosh menyu")
              ]], resize_keyboard=True, one_time_keyboard=True)
        await message.answer("Yuborish kerakmi?", reply_markup=keyboard)


@dp.message_handler(commands=["follow"])
async def following_channel(msg):
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


@dp.message_handler(content_types=["text", "sticker", "photo", "voice", "document", "video", "video_note"])
async def some_text(message: types.Message):
    chat = collchats.find_one({"user_chat_id": message.chat.id})
    if message.text == "🗣 Takliflar":
        await taklif_user_message(message)
    # if message.text == "📝 Ro'yxatdan o'tish":
    #     await account_registration_act(message)
    # elif message.text == "🔖 Anketa":
    #     await account_user(message)
    elif message.text == "🗣 Do'stlarga ulashish":
        await referal_link(message)
    elif message.text == "🏠 Bosh menyu":
        await menu(message)
    # elif message.text == "💣 Anketani o'chirish":
    #     await remove_account_act(message)
    elif message.text == "☕️ Suhbatdosh izlash":
        await search_user_act(message)
    elif message.text == "📛 Izlashni to'xtatish":
        await stop_search_act(message)
    # :TODO next day remove commands
    elif message.text == "📝 Ro'yxatdan o'tish":
        await menu(message)
    elif message.text == "🔖 Anketa":
        await menu(message)
    elif message.text == "💣 Anketani o'chirish":
        await menu(message)
    elif message.text == "✏ Jins":
        await menu(message)
    elif message.text == "✏ Kim bilan suxbatlashish?":
        await menu(message)
    elif message.text == "✏ Tahallusni o'zgartirish":
        await menu(message)
    elif message.text == "✏ Bio":
        await menu(message)
    elif message.text == "✏ Haqimda":
        await menu(message)
    elif message.text == "✏ Jins":
        await menu(message)
    elif message.text == "✏ Kim bilan suxbatlashish?":
        await menu(message)
    elif message.text == "✏ Tahallusni o'zgartirish":
        await menu(message)
    elif message.text == "✏ Bio":
        await menu(message)
    elif message.text == "✏ Haqimda":
        await menu(message)
    # TODO this
    elif message.text == "💔 Suhbatni yakunlash":
        await leave_from_chat_act(message)
    elif message.text == "👍 Ha":
        await yes_rep_act(message)
    elif message.text == "👎 Yo'q":
        await no_rep_act(message)
    elif message.text == "🗣 Shikoyat berish":
        await report_rep_act(message)
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
        else:
            keyboard = ReplyKeyboardMarkup(
                [[KeyboardButton("👍 Ha"), KeyboardButton("👎 Yo'q")],
                 [KeyboardButton("🗣 Shikoyat berish")]], resize_keyboard=True)
            await message.answer("Suhbatdoshingiz chatni tark etgan! Spam qilmang!", reply_markup=keyboard)


@dp.callback_query_handler(text_contains="remove")
async def process_remove_account(callback: types.CallbackQuery):
    collusers.delete_one({"_id": callback.from_user.id})
    await callback.message.answer("Siz muvaffaqiyatli anketangizni o'chirdingiz")
    await menu(callback.message)


@dp.callback_query_handler(text_contains="cancel")
async def process_cancel(callback: types.CallbackQuery):
    await callback.message.answer("Yaxshi, qaytib bunaqa hazil qilmang 😉")


@dp.callback_query_handler(text_contains='channel_subscribe')
async def channel_affirmative_reg(callback_query: types.CallbackQuery):
    if await admin_commands.is_authenticated(callback_query):
        await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
        await menu(callback_query)
    else:
        await callback_query.answer(text="A'zo bo'lmadingiz!", show_alert=True)


if __name__ == "__main__":
    print("Bot ishga tushirilmoqda...")
    executor.start_polling(dp)
