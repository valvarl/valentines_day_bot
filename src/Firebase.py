# ! /usr/bin/env python
# -*- coding: utf-8 -*-

from firebase import firebase as fb
import json

with open('access_data.json') as inf:
    firebase_url = json.load(inf)['firebase_url']

firebase = fb.FirebaseApplication(firebase_url)


def get_valentine(user_id):
    result = firebase.get('/users/%d/' % user_id, 'valentine')
    print(result)
    return result


def set_name(user_id, name, data):
    result = firebase.put('/users/{}/valentine/'.format(user_id), name, data)
    print(result)


def storage_valentine(user_id, to_id=0):
    data = get_valentine(user_id)
    data['from_id'] = user_id
    data['to_id'] = to_id
    data['sent'] = False
    result = firebase.post('/storage/', data)
    print(result)
