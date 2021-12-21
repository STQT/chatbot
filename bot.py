import logging

from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from pymongo import MongoClient
import random

from config import BOT_TOKEN, MONGO_URL

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

cluster = MongoClient(MONGO_URL)
collqueue = cluster.chatbot.queue
collusers = cluster.chatbot.users
collchats = cluster.chatbot.chats


class SetBio(StatesGroup):
    finding = State()
    user_bio = State()
    gender = State()
    nickname = State()


class SetRegBio(StatesGroup):
    finding = State()
    user_bio = State()
    gender = State()


@dp.message_handler(commands="start")
async def menu(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("☕️ Suhbatdosh izlash")
            ],
            [
                KeyboardButton("🔖 Anketa")
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
              KeyboardButton("👤 Muhim emas")
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
            collusers.update_one({"_id": message.from_user.id}, {
                "$set": {"gender": "👤 Muhim emas"}
            })

        await message.answer("Ma'lumotlar saqlandi")
        await state.finish()
        await account_user(message)


@dp.message_handler(commands=["account"])
async def account_user(message: types.Message):
    if collusers.count_documents({"_id": message.from_user.id}) == 0:
        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("📝 Ro'yxatdan o'tish")]], resize_keyboard=True, one_time_keyboard=True)
        await message.answer("Siz tizimda hali ro'yxatdan o'tmagansiz", reply_markup=keyboard)
    else:
        acc = collusers.find_one({"_id": message.from_user.id})
        text = f"👤Foydalanuvchi tahallusi: {acc.get('nickname', 'Mavjud emas')}\n" \
               f"💵 Balans: {acc['balance']}\n" \
               f"Reyting: {acc['reputation']}\n" \
               f"📝Bio: {acc['bio']}\n" \
               f"Jins: {acc.get('gender', 'Noaniq')}\n" \
               f"Qidiruv: {acc.get('finding', 'Noaniq')}"
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
                    KeyboardButton("✏ Jinsni o'zgartirish"),
                    KeyboardButton("✏ Kim bilan suxbatlashish?"),
                ],
                [
                    KeyboardButton("✏ Tahallusni o'zgartirish"),
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
                "nickname": message.from_user.username,
                "balance": 0,
                "reputation": 0,
                "bio": "Tarmoqdagi foydalanuvchilardan biri"
            }
        )
        # hearts = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍"]
        await SetRegBio.user_bio.set()
        await message.answer(f"Salom, {message.from_user.username}\nO'zingiz haqingizda yozing")
        # await message.answer(f"{random.choice(hearts)} Siz tizimda muvaffaqiyatli anketangizni yaratdingiz ☺️")
        # await account_user(message)
    else:
        await message.answer("Siz tizimda allaqachon anketa yaratgansiz 😉")
        await account_user(message)


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
              KeyboardButton("👤 Muhim emas")
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
            collusers.update_one({"_id": message.from_user.id}, {
                "$set": {"gender": "👤 Muhim emas"}
            })

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
        # await state.finish()
        await account_user(message)


@dp.message_handler(commands=["search_user", "searchuser"])
async def search_user_act(message: types.Message):
    if message.chat.type == "private":
        if collusers.count_documents({"_id": message.from_user.id}) == 0:
            await account_user(message)
        else:
            if collchats.count_documents({"user_chat_id": message.chat.id}) != 0:
                keyboard = ReplyKeyboardMarkup(
                    [[KeyboardButton("💔 Suhbatni yakunlash")]], resize_keyboard=True, one_time_keyboard=True)
                await message.answer("Siz hozirda kim bilandir suhbatlashyapsiz", reply_markup=keyboard)
            else:
                if collqueue.count_documents({"_id": message.chat.id}) != 1:
                    keyboard = ReplyKeyboardMarkup(
                        [[KeyboardButton("📛 Izlashni to'xtatish")]], resize_keyboard=True)
                    finder_acc = collusers.find_one({"_id": message.from_user.id})
                    interlocutor = collqueue.find_one({"_sex": finder_acc.get('finding'),
                                                       "_finding": finder_acc.get('gender')})
                    if interlocutor is None:
                        user_gender_var = finder_acc.get('gender')
                        user_find = finder_acc.get('finding')
                        if user_find == "👤 Muhim emas":
                            interlocutor = collqueue.find_one(
                                {
                                    "_sex": {
                                        "$in":
                                            ["👤 Muhim emas",
                                             "👩‍ Ayol kishi",
                                             "👨‍ Yigit kishi"]
                                    },
                                    "_finding": {
                                        "$in":
                                            [finder_acc.get('gender'),
                                             "👤 Muhim emas"]
                                    }
                                })
                        elif user_gender_var == "👤 Muhim emas":
                            interlocutor = collqueue.find_one(
                                {
                                    "_sex": finder_acc.get('finding'),
                                    "$or":
                                        [
                                            {"_finding": "👤 Muhim emas"},
                                            {"_finding": "👩‍ Ayol kishi"},
                                            {"_finding": "👨‍ Yigit kishi"}
                                        ],
                                })
                        elif user_gender_var == "👤 Muhim emas" and user_find == "👤 Muhim emas":
                            interlocutor = collqueue.find_one({})
                    if interlocutor is None:
                        acc = collusers.find_one({"_id": message.from_user.id})
                        collqueue.insert_one({
                            "_id": message.chat.id,
                            "_sex": acc.get('gender'),
                            "_finding": acc.get('finding')
                        })
                        await message.answer(
                            "🕒 Suhbatdoshni izlash boshlandi, iltimos biroz kuting... "
                            "Yoki izlashni to'xtatishingiz mumkin", reply_markup=keyboard)
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
                            nickname_intestlocutor = collusers.find_one(
                                {"_id": message.chat.id})["nickname"]
                            bio_intestlocutor = collusers.find_one(
                                {"_id": message.chat.id})["bio"]
                            gender_intestlocutor = collusers.find_one(
                                {"_id": message.chat.id}).get("gender", "Noaniq")
                            bio_user = collusers.find_one({"_id": collchats.find_one(
                                {"user_chat_id": message.chat.id})["interlocutor_chat_id"]})["bio"]
                            nickname_user = collusers.find_one({"_id": collchats.find_one(
                                {"user_chat_id": message.chat.id})["interlocutor_chat_id"]})["nickname"]
                            gender_user = collusers.find_one({"_id": collchats.find_one(
                                {"user_chat_id": message.chat.id})["interlocutor_chat_id"]}).get("gender", "Noaniq")
                            keyboard_leave = ReplyKeyboardMarkup([[
                                KeyboardButton(
                                    "💔 Suhbatni yakunlash")]],
                                resize_keyboard=True, one_time_keyboard=True)
                            chat_info = collchats.find_one({"user_chat_id": message.chat.id})[
                                "interlocutor_chat_id"]

                            await message.answer(
                                "Suhbatdosh topildi!😉\n"
                                "Suhbatni boshlashingiz mumkin.🥳\n"
                                f"\nSuhbatdoshingiz tahallusi: {nickname_user}\n"
                                f"Suhbatdoshingiz biosi: {bio_user}\n"
                                f"Suhbatdoshingiz jinsi: {gender_user}",
                                reply_markup=keyboard_leave)
                            await bot.send_message(
                                text="Suhbatdosh topildi!😉\n"
                                     "Suhbatni boshlashingiz mumkin.🥳\n\n"
                                     f"Suhbatdosh tahallusi: {nickname_intestlocutor}\n"
                                     f"Suhbatdosh biosi: {bio_intestlocutor}\n"
                                     f"Suhbatdosh jinsi: {gender_intestlocutor}",
                                chat_id=chat_info,
                                reply_markup=keyboard_leave)
                        else:
                            collqueue.insert_one({"_id": message.chat.id})
                            await message.answer(
                                "🕒 Suhbatdoshni izlash boshlandi, iltimos biroz kuting... "
                                "Yoki izlashni to'xtatishingiz mumkin", reply_markup=keyboard)

                else:
                    keyboard = ReplyKeyboardMarkup(
                        [[KeyboardButton("📛 Izlashni to'xtatish")]], resize_keyboard=True)
                    await message.answer("Siz suhbatdosh izlayapsiz, biroz sabr qiling 🕒😉", reply_markup=keyboard)


@dp.message_handler(commands=["stop_search"])
async def stop_search_act(message: types.Message):
    if collqueue.count_documents({"_id": message.chat.id}) != 0:
        collqueue.delete_one({"_id": message.chat.id})
        await menu(message)
    else:
        await message.answer("Siz suhbatdosh izlamayapsiz")
        await menu(message)


@dp.message_handler(commands=["Ha"])
async def yes_rep_act(message: types.Message):
    if collchats.count_documents({"user_chat_id": message.chat.id}) != 0:
        collusers.update_one({"_id": message.from_user.id}, {
            "$inc": {"reputation": 5}})
        collchats.delete_one({"user_chat_id": message.chat.id})
        await message.answer("Javobingiz uchun rahmat!☺️")
        await menu(message)
    else:
        await message.answer("Siz suhbatdosh bilan yozishmayapsiz")


@dp.message_handler(commands=["Yo'q"])
async def no_rep_act(message: types.Message):
    if collchats.count_documents({"user_chat_id": message.chat.id}) != 0:
        collusers.update_one({"_id": collchats.find_one({"user_chat_id": message.chat.id})[
            "interlocutor_chat_id"]}, {"$inc": {"reputation": -5}})
        collchats.delete_one({"user_chat_id": message.chat.id})
        await message.answer("Javobingiz uchun rahmat!☺️")
        await menu(message)
    else:
        await message.answer("Siz suhbatdosh bilan yozishmayapsiz")


@dp.message_handler(commands=["rep_menu"])
async def rep_menu(message: types.Message):
    if collchats.count_documents({"user_chat_id": message.chat.id}) != 0:
        keyboard = ReplyKeyboardMarkup(
            [
                [
                    KeyboardButton("👍 Ha"),
                    KeyboardButton("👎 Yo'q")
                ]
            ],
            resize_keyboard=True
        )
        await message.answer("Suhbatdosh bilan muloqot maroqli o'tdimi?", reply_markup=keyboard)
        # await account_user(message)
    else:
        await message.answer("Siz suhbatdosh bilan yozishmayapsiz")


@dp.message_handler(commands=["yakunlash", "leave", "leave_chat"])
async def leave_from_chat_act(message: types.Message):
    if collchats.count_documents({"user_chat_id": message.chat.id}) != 0:
        await message.answer("Siz chatni tark etdingiz")
        keyboard = ReplyKeyboardMarkup(
            [
                [
                    KeyboardButton("👍 Ha"),
                    KeyboardButton("👎 Yo'q")
                ]
            ],
            resize_keyboard=True
        )
        try:
            await bot.send_message(text="Suhbatdoshingiz chatni tark etdi",
                                   chat_id=collchats.find_one(
                                       {"user_chat_id": message.chat.id}).get("interlocutor_chat_id"),
                                   reply_markup=keyboard)
            await bot.send_message(text="Suhbatdosh bilan muloqot maroqli o'tdimi?",
                                   chat_id=collchats.find_one(
                                       {"user_chat_id": message.chat.id}).get("interlocutor_chat_id"),
                                   reply_markup=keyboard)
            await rep_menu(message)
            # TODO: NEED delete user from collchats. Ja unchalik muhim emas, lekin ortiqcha malumotlar qoladi
        except Exception as e:
            await account_user(message)
            logging.error(f"Ushbu foydalanuvchida xato yuz berdi: {e}")

    else:
        await message.answer("Siz suhbatdosh bilan yozishmayapsiz")


@dp.message_handler(content_types=["text", "sticker", "photo", "voice", "document"])
async def some_text(message: types.Message):
    if message.text == "📝 Ro'yxatdan o'tish":
        await account_registration_act(message)
    elif message.text == "🔖 Anketa":
        await account_user(message)
    elif message.text == "🏠 Bosh menyu":
        await menu(message)
    elif message.text == "💣 Anketani o'chirish":
        await remove_account_act(message)
    elif message.text == "☕️ Suhbatdosh izlash":
        await search_user_act(message)
    elif message.text == "📛 Izlashni to'xtatish":
        await stop_search_act(message)
    elif message.text == "✏ Jinsni o'zgartirish":
        await user_gender(message)
    elif message.text == "✏ Kim bilan suxbatlashish?":
        await user_finding(message)
    elif message.text == "✏ Tahallusni o'zgartirish":
        await user_tahallus(message)
    elif message.text == "✏ Bio":
        await user_bio(message)
    elif message.text == "💔 Suhbatni yakunlash":
        await leave_from_chat_act(message)
    elif message.text == "👍 Ha":
        await yes_rep_act(message)
    elif message.text == "👎 Yo'q":
        await no_rep_act(message)
    elif message.content_type == "sticker":
        try:
            await bot.send_sticker(
                chat_id=collchats.find_one({"user_chat_id": message.chat.id})["interlocutor_chat_id"],
                sticker=message.sticker["file_id"])
        except TypeError:
            pass
    elif message.content_type == "photo":
        try:
            await bot.send_photo(
                chat_id=collchats.find_one({"user_chat_id": message.chat.id})["interlocutor_chat_id"],
                photo=message.photo[len(message.photo) - 1].file_id)
        except TypeError:
            pass
    elif message.content_type == "voice":
        try:
            await bot.send_voice(
                chat_id=collchats.find_one({"user_chat_id": message.chat.id})["interlocutor_chat_id"],
                voice=message.voice["file_id"])
        except TypeError:
            pass
    elif message.content_type == "document":
        try:
            await bot.send_document(
                chat_id=collchats.find_one({"user_chat_id": message.chat.id})["interlocutor_chat_id"],
                document=message.document["file_id"])
        except TypeError:
            pass
    else:
        try:
            await bot.send_message(
                text=message.text,
                chat_id=collchats.find_one({"user_chat_id": message.chat.id})["interlocutor_chat_id"])
        except TypeError:
            pass


@dp.callback_query_handler(text_contains="remove")
async def process_remove_account(callback: types.CallbackQuery):
    collusers.delete_one({"_id": callback.from_user.id})
    await callback.message.answer("Siz muvaffaqiyatli anketangizni o'chirdingiz")
    await menu(callback.message)


@dp.callback_query_handler(text_contains="cancel")
async def process_cancel(callback: types.CallbackQuery):
    await callback.message.answer("Yaxshi, qaytib bunaqa hazil qilmang 😉")


if __name__ == "__main__":
    print("Bot ishga tushirilmoqda...")
    executor.start_polling(dp)
