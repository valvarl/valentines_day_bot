# ! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
from src.ValentinesDayBot import ValentinesDayBot

if __name__ == '__main__':
    with open('access_data.json', encoding='utf8') as inf:
        data = json.load(inf)
        group_token = data['group_token']
        group_id = data['group_id']
        post_id = data['post_id']
        email = data['email']
        password = data['password']
        st1_start = data['st1_start']
        st2_start = data['st2_start']

    vdb = ValentinesDayBot(group_token, group_id, post_id, email, password, st1_start, st2_start)
    vdb.start()
