# ! /usr/bin/env python
# -*- coding: utf-8 -*-

from firebase import firebase as fb
import json

with open('access_data.json') as inf:
    firebase_url = json.load(inf)['firebase_url']

firebase = fb.FirebaseApplication(firebase_url)


def init_user(user_id):
    result = firebase.post('/in_system/', user_id)
    # print(result)


def get_valentine(user_id):
    result = firebase.get('/users/%d/' % user_id, 'valentine')
    # print(result)
    return result


def expect_valentine(user_id):
    result = firebase.get('/awaiting_dispatch/', user_id)
    if result:
        new = []
        for v in result.values():
            res = firebase.get('/storage/', v)
            if not res['sent']:
                res['storage_url'] = v
                new.append(res)
        return new
    else:
        return None


def set_name(user_id, name, data):
    result = firebase.put('/users/{}/valentine/'.format(user_id), name, data)
    # print(result)


def storage_valentine(user_id, to_id, to_name):
    data = get_valentine(user_id)
    data['from_id'] = user_id
    data['to_id'] = to_id
    data['to_name'] = to_name
    data['sent'] = False
    result = firebase.post('/storage/', data)
    storage_link = result['name']
    # print(result)
    if to_id:
        result = firebase.post('/awaiting_dispatch/%d' % to_id, storage_link)
        # print(result)
    return data, storage_link


def users_in_system():
    result = firebase.get('', 'in_system')
    # print(result)
    return list(result.values()) if result else []


def archive(valentine):
    result = firebase.post('/archive/', valentine)
    # print(result)


def mark_sent(storage_link):
    result = firebase.put('/storage/{}/'.format(storage_link), 'sent', True)
    # print(result)


def get_valentines():
    result = firebase.get('', 'storage')
    return result
