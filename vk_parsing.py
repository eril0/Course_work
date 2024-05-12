import requests
import json

def get_user_info(user_ids, fields, access_token, v='5.131'):
    """
    Получение информации о пользователях VK

    :param user_ids: список идентификаторов пользователей
    :param fields: список полей профиля, которые нужно получить
    :param access_token: токен доступа
    :param v: версия API
    :return: словарь с данными пользователей
    """
    user_info_url = "https://api.vk.com/method/users.get"
    responses = []
    for batch in [user_ids[i:i + 100] for i in range(0, len(user_ids), 100)]:
        params = {
            'user_ids': ",".join(map(str, batch)),
            'fields': ",".join(fields),
            'access_token': access_token,
            'v': v
        }
        response = requests.get(user_info_url, params=params)
        if response.status_code == 200:
            data = response.json()
            if 'response' in data:
                responses.extend(data['response'])
    return responses


def get_group_members(group_ids, access_token, version='5.131'):
    api_url = "https://api.vk.com/method/groups.getMembers"
    members_per_groups = []
    offset = 0
    count = 1000  # Максимально допустимое значение
    for group_id in group_ids:
        members=[]
        while True:
            params = {
                'group_id': group_id,
                'access_token': access_token,
                'v': version,
                'offset': offset,
                'count': count
            }
            response = requests.get(api_url, params=params)
            data = response.json()

            if 'error' in data:
                print("VK API Error:", data['error']['error_msg'])
                break

            members.extend(data['response']['items'])
            
            if len(data['response']['items']) < count:
                break

            offset += count
        members_per_groups.append(members)


    return members_per_groups

def transform_user_data(user):
    # Извлечение и обработка данных города
    if 'city' in user and isinstance(user['city'], dict):
        user['city'] = user['city'].get('id')
    
    # Обработка образовательной информации
    if 'education' in user and isinstance(user['education'], dict):
        user['university'] = user['education'].get('university', 0)
        user['faculty'] = user['education'].get('faculty', 0)
        del user['education']  # Удаляем исходный ключ education

    # Обработка карьеры
    if 'career' in user and isinstance(user['career'], list) and user['career']:
        career_data = user['career'][0]
        user['career'] = career_data.get('group_id', career_data.get('company', ''))
        user['position'] = career_data.get('position', '')

    # Обработка школ
    if 'schools' in user and isinstance(user['schools'], list) and user['schools']:
        school_data = user['schools'][0]
        user['schools'] = school_data.get('id')
        user['class'] = school_data.get('class', '')
        user['year_from'] = school_data.get('year_from', '')

    return user

def get_friends_list(access_token, user_id=None):
    """ Получить список друзей пользователя ВКонтакте.

    :param access_token: токен доступа
    :param user_id: ID пользователя ВК, список друзей которого нужно получить
                    Если None, возвращается список друзей текущего пользователя
    :return: список друзей в формате списка словарей {id, first_name, last_name}
    """
    url = 'https://api.vk.com/method/friends.get'
    params = {
        'access_token': access_token,
        'user_id': user_id,
        'fields': 'id',
        'v': '5.131'  # Указываем версию API ВКонтакте
    }

    response = requests.get(url, params=params)
    
    try:
        response.raise_for_status()
        data = response.json()
        if 'error' in data:
            print(f"Ошибка VK API: {data['error']['error_msg']} у пользователя {user_id}")
            return []
        ret=data['response']['items']
        for i in range(len(ret)):
            user_corrected=str(ret[i]['id'])
            ret[i]=user_corrected
        return ret
            

            
    except (requests.RequestException, ValueError) as e:
        print(f"Ошибка при получении списка друзей у {user_id}: {e} ")
        return []

def get_user_subscriptions(user_id, access_token):
    """
    Получает список подписок пользователя ВКонтакте.

    Параметры:
    user_id : int or str
        Идентификатор пользователя, о котором нужно получить информацию.
    access_token : str
        Токен доступа для авторизации запроса к API ВКонтакте.

    Возвращает:
    subscriptions : dict
        Словарь с информацией о подписках пользователя.
    """

    # Базовый URL для API VK
    url = 'https://api.vk.com/method/users.getSubscriptions'

    # Параметры для отправки GET-запроса
    params = {
        'user_id': user_id,
        'access_token': access_token,
        'extended': 1,  # 1 - возвращает расширенную информацию о группах и пользователях
        'v': '5.131'    # версия API
    }

    # Выполнение GET-запроса
    response = requests.get(url, params=params)
    try:
        response.raise_for_status()
        data = response.json()
        if 'error' in data:
            print(f"Ошибка VK API: {data['error']['error_msg']} у пользователя {user_id}")
            return []
        data=data['response']['items']
        ret = [d['id'] for d in data]
        return ret
            
    except (requests.RequestException, ValueError) as e:
        print(f"Ошибка при получении списка друзей у {user_id}: {e} ")
        return []
    

group_ids = ['21585301','197213300','rebyata_1580','itbda2022','podslushano2006']
access_token = '62e1271562e1271562e127155461f910d2662e162e1271504d9f51135047845c9f03919'
members = get_group_members(group_ids, access_token)

all_users_info=[]
fields = ['sex','bdate', 'city', 'education','career','schools','can_send_friend_request','can_write_private_message','followers_count']

for group_mem in members:
    all_users_info.append(get_user_info(group_mem,fields,access_token))


all_users_info_corrected=[]
for group_mem in all_users_info:
    transformed_data=[transform_user_data(user) for user in group_mem]
    for i in range(len(transformed_data)):
        user_corrected=dict()
        for k,v in transformed_data[i].items():
            if k in ['id','bdate','city','career','university','faculty','schools','sex','position','class','year_from','can_send_friend_request','can_write_private_message','followers_count']:
                user_corrected[k]=v
        user_corrected['friends']=get_friends_list(access_token, transformed_data[i]['id'])
        user_corrected['subscriptions'] = get_user_subscriptions(transformed_data[i]['id'],access_token)
        transformed_data[i]=user_corrected
    all_users_info_corrected.append(transformed_data)


# Путь к файлу, в который будут сохранены данные
filename1 = 'group1.json'
filename2 = 'group2.json'
filename3 = 'group3.json'
filename4 = 'group4.json'
filename5 = 'group5.json'

# Сохранение в файл JSON
with open(filename1, 'w') as f:
    json.dump(all_users_info_corrected[0], f)
with open(filename2, 'w') as f:
    json.dump(all_users_info_corrected[1], f)
with open(filename3, 'w') as f:
    json.dump(all_users_info_corrected[2], f)
with open(filename4, 'w') as f:
    json.dump(all_users_info_corrected[3], f)
with open(filename5, 'w') as f:
    json.dump(all_users_info_corrected[4], f)