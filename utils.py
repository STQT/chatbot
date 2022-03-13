from bot import collusers


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