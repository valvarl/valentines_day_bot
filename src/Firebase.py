# ! /usr/bin/env python
# -*- coding: utf-8 -*-

from firebase import firebase as fb
import json

with open('access_data.json') as inf:
    firebase_url = json.load(inf)['firebase_url']

firebase = fb.FirebaseApplication(firebase_url)


def init_user(user_id):
    result = firebase.post('/in_system/', user_id)
    print(result)


def get_valentine(user_id):
    result = firebase.get('/users/%d/' % user_id, 'valentine')
    print(result)
    return result


def expect_valentine(user_id):
    result = firebase.get('/awaiting_dispatch/', user_id)
    if result:
        res = firebase.get('/storage/', result)
        firebase.put('/storage/{}/'.format(result), 'sent', True)
        return res
    else:
        return None


def set_name(user_id, name, data):
    result = firebase.put('/users/{}/valentine/'.format(user_id), name, data)
    print(result)


def storage_valentine(user_id, to_id, to_name):
    data = get_valentine(user_id)
    data['from_id'] = user_id
    data['to_id'] = to_id
    data['to_name'] = to_name
    data['sent'] = False
    result = firebase.post('/storage/', data)
    print(result)
    if to_id:
        result = firebase.put('/awaiting_dispatch/', user_id, result['name'])
        print(result)
    result = firebase.get('', 'in_system')
    print(result)
    return to_id and to_id not in (result.values() if result else [])


def try_to_send_vk():
    pass


def force_send():
    pass
