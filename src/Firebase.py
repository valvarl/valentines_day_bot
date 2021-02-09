# ! /usr/bin/env python
# -*- coding: utf-8 -*-

from firebase import firebase as fb
import json

with open('access_data.json') as inf:
    firebase_url = json.load(inf)['firebase_url']

firebase = fb.FirebaseApplication(firebase_url)


def new_valentine(user_id):
    data = {
        'name': '',
        'enum': [],
        'choice': -1,
        'photo': '',
        'sign': '',
        'paragraph': '',
        'url': '',
        'email': '',
        'ready': False,
        'sent': False
    }
    result = firebase.post('/users/%d' % user_id, data)
    print(result)


def get_valentines(user_id):
    result = firebase.get('/users/%d' % user_id)
    print(result)
    return result


def set_name(user_id, name):
    last_valentine = get_valentines(user_id).keys()[-1]
    data = {
        'name': name
    }
    result = firebase.post('/users/{}/{}'.format(user_id, last_valentine), data)
    print(result)
