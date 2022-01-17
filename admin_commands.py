import logging

from bot import collusers, collqueue, collchats, bot
from aiogram.utils.exceptions import ChatNotFound


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
    text = f'👩: {len(ladys_list)}\n👨: {len(mans_list)}\n👤: {len(another_list)}\nBlocked: {blocked}'
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


async def send_post_all_users(data, users):
    if data['type'] == 'voice':
        for i in users:
            try:
                await bot.send_voice(chat_id=i, voice=data['voice'], caption=data['caption'],
                                     caption_entities=data['caption_entities'])
            except ChatNotFound:
                collusers.update_one({"_id": i}, {"$set": {"status": False}})
                logging.warning(f"Ushbu {i} foydalanuvchi botni bloklagan")
    elif data['type'] == 'text':
        for i in users:
            try:
                await bot.send_message(chat_id=i, text=data['text'], entities=data['entities'])
            except ChatNotFound:
                collusers.update_one({"_id": i}, {"$set": {"status": False}})
                logging.warning(f"Ushbu {i} foydalanuvchi botni bloklagan")
    elif data['type'] == 'video':
        for i in users:
            try:
                await bot.send_video(chat_id=i, video=data['video'], caption=data['caption'],
                                     caption_entities=data['caption_entities'])
            except ChatNotFound:
                collusers.update_one({"_id": i}, {"$set": {"status": False}})
                logging.warning(f"Ushbu {i} foydalanuvchi botni bloklagan")
    elif data['type'] == 'photo':
        for i in users:
            try:
                await bot.send_photo(chat_id=i, photo=data['photo'], caption=data['caption'],
                                     caption_entities=data['caption_entities'])
            except ChatNotFound:
                collusers.update_one({"_id": i}, {"$set": {"status": False}})
                logging.warning(f"Ushbu {i} foydalanuvchi botni bloklagan")
    elif data['type'] == 'sticker':
        for i in users:
            try:
                await bot.send_sticker(chat_id=i, sticker=data['sticker'])
            except ChatNotFound:
                collusers.update_one({"_id": i}, {"$set": {"status": False}})
                logging.warning(f"Ushbu {i} foydalanuvchi botni bloklagan")
    elif data['type'] == 'document':
        for i in users:
            try:
                await bot.send_document(chat_id=i, document=data['document'], caption=data['caption'],
                                        caption_entities=data['caption_entities'])
            except ChatNotFound:
                collusers.update_one({"_id": i}, {"$set": {"status": False}})
                logging.warning(f"Ushbu {i} foydalanuvchi botni bloklagan")
