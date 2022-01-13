from bot import collusers, collqueue, collchats

pipeline = [{'$lookup':
                 {'from': 'chats',
                  'localField': '_id',
                  'foreignField': 'references',
                  'as': 'cellmodels'}},
            ]


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
    text = f'👩: {len(ladys_list)}\n👨: {len(mans_list)}\n👤: {len(another_list)}'
    return text


async def chat_statistics():
    x = collqueue.find()
    # print("first")
    # collqueue.aggregate()
    # print("second")
    list1 = [a for a in x]
    return list1


async def queue_statistics():
    x = collchats.find()
    list1 = [a for a in x]
    return list1
