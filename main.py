# ! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
import traceback
from time import sleep
from src.ValentinesDayBot import ValentinesDayBot


def logs(s: str):
    with open('logs.txt', 'a+', encoding='utf8') as df:
        df.write(s + '\n')


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
    while True:
        try:
            vdb.start()
        except Exception as e:
            logs('Error:\n' + traceback.format_exc())
            sleep(2)
