import asyncio
import logging

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.exceptions import BotBlocked, BotKicked, UserDeactivated

from bot import collusers, collqueue, collchats, bot


async def user_statistics():
    x = collusers.find()
    user_list = [a for a in x]
    ladys_list = []
    mans_list = []
    another_list = []
    for i in user_list:
        gender = i.get('gender')
        if gender == '👩\u200d Ayol kishi':
            ladys_list.append(i)
        elif gender == '👨\u200d Yigit kishi':
            mans_list.append(i)
        else:
            another_list.append(i)
    blocked = collusers.count_documents({"status": False})
    text = f'👩: {len(ladys_list)}\n👨: {len(mans_list)}\nJinsni kiritmaganlar: {len(another_list)}\nBlocked: {blocked}'
    return text


async def queue_statistics():
    x = collqueue.find()
    user_list = [a for a in x]
    ladys_list = []
    mans_list = []
    another_list = []
    for i in user_list:
        gender = i.get('_sex')
        if gender == '👩\u200d Ayol kishi':
            ladys_list.append(i)
        elif gender == '👨\u200d Yigit kishi':
            mans_list.append(i)
        else:
            another_list.append(i)
    text = f'👩: {len(ladys_list)}\n👨: {len(mans_list)}\n👤: {len(another_list)}\n'
    return text


async def chat_statistics():
    x = collchats.find()
    list1 = [a for a in x]
    return list1


async def get_all_active_users():
    users_id = collusers.find()
    tg_users_id = []
    for i in users_id:
        if i.get("status", True):
            tg_users_id.append(i.get("_id", 0))
    return tg_users_id


async def get_all_inactive_users():
    user_list = []
    chats_inactive = collchats.find()
    if chats_inactive:
        for user in chats_inactive:
            user_list.append(user.get("user_chat_id", 0))
    queue_inactive = collqueue.find()
    if queue_inactive:
        for user in queue_inactive:
            user_list.append(user.get("_id", 0))
    users_id = collusers.find({"_id": {"$nin": list(set(user_list))}})
    tg_users_id = []
    for i in users_id:
        if i.get("status", True):
            tg_users_id.append(i.get("_id", 0))
    return tg_users_id


async def send_post_all_users(data, users):
    if data['type'] == 'voice':
        for i in users:
            try:
                await bot.send_voice(chat_id=i, voice=data['voice'], caption=data['caption'],
                                     caption_entities=data['caption_entities'])
                await asyncio.sleep(0.04)
            except (BotKicked, BotBlocked, UserDeactivated):
                await user_blocked_with_posting(i)
    elif data['type'] == 'text':
        for i in users:
            try:
                keyboard = ReplyKeyboardMarkup(
                    [
                        [
                            KeyboardButton("☕️ Suhbatdosh izlash")
                        ],
                        [
                            KeyboardButton("🗣 Takliflar")
                        ]], resize_keyboard=True, one_time_keyboard=True)
                await bot.send_message(chat_id=i, text=data['text'], entities=data['entities'], reply_markup=keyboard)
                await asyncio.sleep(0.04)
            except (BotKicked, BotBlocked, UserDeactivated):
                await user_blocked_with_posting(i)
    elif data['type'] == 'video':
        for i in users:
            try:
                await bot.send_video(chat_id=i, video=data['video'], caption=data['caption'],
                                     caption_entities=data['caption_entities'])
                await asyncio.sleep(0.04)
            except (BotKicked, BotBlocked, UserDeactivated):
                await user_blocked_with_posting(i)
    elif data['type'] == 'photo':
        for i in users:
            try:
                await bot.send_photo(chat_id=i, photo=data['photo'], caption=data['caption'],
                                     caption_entities=data['caption_entities'])
                await asyncio.sleep(0.04)
            except (BotKicked, BotBlocked, UserDeactivated):
                await user_blocked_with_posting(i)
    elif data['type'] == 'sticker':
        for i in users:
            try:
                await bot.send_sticker(chat_id=i, sticker=data['sticker'])
                await asyncio.sleep(0.04)
            except (BotKicked, BotBlocked, UserDeactivated):
                await user_blocked_with_posting(i)
    elif data['type'] == 'document':
        for i in users:
            try:
                await bot.send_document(chat_id=i, document=data['document'], caption=data['caption'],
                                        caption_entities=data['caption_entities'])
                await asyncio.sleep(0.04)
            except (BotKicked, BotBlocked, UserDeactivated):
                await user_blocked_with_posting(i)


async def user_are_blocked_bot(message):
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("☕️ Suhbatdosh izlash")],
            [KeyboardButton("🔖 Anketa")]
        ], resize_keyboard=True)
    await message.answer("Ushbu foydalanuvchi botni tark etdi :( Boshqa suhbatdoshni qidiring!", reply_markup=keyboard)
    collchats.delete_one({"user_chat_id": message.chat.id})
    collchats.update_many({"interlocutor_chat_id": message.chat.id}, {"$set": {"status": False}})
    collusers.update_one(
        {"_id": collchats.find_one({"user_chat_id": message.chat.id})["interlocutor_chat_id"]},
        {"$set": {"status": False}})


async def user_blocked_with_posting(user):
    collusers.update_one({"_id": user}, {"$set": {"status": False}})
    logging.warning(f"Ushbu {user} foydalanuvchi botni bloklagan")
