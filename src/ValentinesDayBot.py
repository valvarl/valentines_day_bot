# ! /usr/bin/env python
# -*- coding: utf-8 -*-

import vk_api
import vk_api.exceptions
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import random
import requests
from src.Firebase import *
from datetime import datetime, timedelta

with open('src/phrases.json', encoding='utf8') as inf:
    phrases = json.load(inf)

with open('src/valentines.json', encoding='utf8') as inf:
    valentines = json.load(inf)


class ValentinesDayBot:
    def __init__(self, group_token, group_id, post_id):
        self.group_id = group_id
        self.post_id = post_id

        self.bot_session = vk_api.VkApi(token=group_token)
        self.bot_api = self.bot_session.get_api()
        print('ready')

    def start(self):
        longpoll = VkBotLongPoll(self.bot_session, self.group_id)
        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW and event.from_user:
                print(event.message)
                from_id = event.message['from_id']
                message_id = event.message['id']
                message = event.message['text'].lower()
                if message in ['начать', 'start']:
                    if event.message['conversation_message_id'] != 1:
                        valentine = get_valentine(from_id)
                        if valentine and 'remain' in valentine.keys():
                            if valentine['remain'] > 0:
                                self.send_message(from_id, phrases['name'])
                            else:
                                self.send_message(from_id, phrases['all_sent'])
                        else:
                            init_user(from_id)
                            set_name(from_id, 'remain', 3)
                            self.send_message(from_id, phrases['greeting'], keyboard='start')
                    else:
                        init_user(from_id)
                        set_name(from_id, 'remain', 3)
                        self.send_message(from_id, phrases['greeting'], keyboard='start')
                elif message == 'да':
                    context = self.get_context(from_id, message_id)
                    if context[-1]['text'] == phrases['greeting'] and get_valentine(from_id)['remain'] > 0:
                        self.send_message(from_id, phrases['name'])
                    elif context[-1]['text'] == phrases['privacy']:
                        set_name(from_id, 'sign', '')
                        self.send_message(from_id, phrases['look1'], keyboard='no-yes')
                    elif context[-1]['text'] == phrases['look1']:
                        self.send_message(from_id, phrases['paragraph'], keyboard='skip')
                    elif context[-1]['text'] == phrases['look2']:
                        self.send_message(from_id, phrases['url1'] +
                                          get_valentine(from_id)['name'] + phrases['url2'], keyboard='skip')
                    elif context[-1]['text'] == phrases['contacts']:
                        self.send_message(from_id, phrases['url1'] +
                                          get_valentine(from_id)['name'] + phrases['url2'], keyboard='skip')
                    elif context[-1]['text'] == phrases['look3']:
                        valentine = get_valentine(from_id)
                        remain = valentine['remain']-1
                        set_name(from_id, 'remain', remain)
                        to_id, to_name = self.get_user(valentine['url'])
                        valentine = storage_valentine(from_id, to_id, to_name)
                        user_in_system = check_user(to_id)
                        now = datetime.utcnow() + timedelta(hours=3)
                        if now >= datetime(2021, 2, 14, 22):
                            self.force_send(valentine)
                        elif to_id:
                            if now.day >= 14:
                                if user_in_system:
                                    self.try_to_send_vk(valentine)
                                else:
                                    self.tag_user(self.bot_session, to_id, to_name)
                            elif not user_in_system:
                                self.tag_user(self.bot_session, to_id, to_name)

                        set_name(from_id, 'ready', True)
                        if remain > 0:
                            self.send_message(from_id, phrases['finish1'] + phrases['finish2'] +
                                              ['одну', 'две'][remain-1] + phrases['finish3'], keyboard='start3')
                        else:
                            self.send_message(from_id, self.phrases['finish1'] + self.phrases['finish4'])
                elif message == 'нет':
                    context = self.get_context(from_id, message_id)
                    if context[-1]['text'] == phrases['privacy']:
                        self.send_message(from_id, phrases['pseudonym'])
                    elif context[-1]['text'] == phrases['look1'] and get_valentine(from_id)['remain'] > 0:
                        self.send_message(from_id, phrases['finish3'][2:], keyboard='start2')
                    elif context[-1]['text'] == phrases['look2']:
                        set_name(from_id, 'paragraph', '')
                        self.send_message(from_id, phrases['url1'] +
                                          get_valentine(from_id)['name'] + phrases['url2'], keyboard='skip')
                    elif context[-1]['text'] == phrases['look3']:
                        self.send_message(from_id, phrases['url1'] +
                                          get_valentine(from_id)['name'] + phrases['url2'], keyboard='skip')
                elif message == 'пропустить':
                    context = self.get_context(from_id, message_id)
                    if context[-1]['text'] in [phrases['paragraph'], phrases['again2']]:
                        set_name(from_id, 'paragraph', '')
                        self.send_message(from_id, phrases['url1'] +
                                          get_valentine(from_id)['name'] + phrases['url2'], keyboard='skip')
                    elif context[-1]['text'].startswith(phrases['url1']) and \
                            context[-1]['text'].endswith(phrases['url2']):
                        set_name(from_id, 'url', '')
                        self.send_message(from_id, phrases['email1'] +
                                          get_valentine(from_id)['name'] + phrases['email2'], keyboard='skip')
                    elif context[-1]['text'].startswith(phrases['email1']) and \
                            context[-1]['text'].endswith(phrases['email2']):
                        set_name(from_id, 'email', '')
                        valentine = get_valentine(from_id)
                        if valentine['url'] or valentine['email']:
                            self.send_message(from_id, phrases['look3'], keyboard='look3')
                        else:
                            self.send_message(from_id, phrases['contacts'], keyboard='contacts')
                elif message == 'нет, я жду свою валентиночку':
                    context = self.get_context(from_id, message_id)
                    if context[-1]['text'] == phrases['greeting'] or \
                            context[-1]['text'].endswith(phrases['finish3'][2:]):
                        valentine = expect_valentine(from_id)
                        if valentine:
                            now = datetime.utcnow() + timedelta(hours=3)
                            if now.day >= 10:
                                for v in valentine:
                                    self.send_message(from_id, json.dumps(v))
                                self.send_message(from_id, phrases['received'], keyboard='start2')
                            else:
                                self.send_message(from_id, phrases['not_send'], keyboard='start2')
                        else:
                            self.send_message(from_id, phrases['not_expect'], keyboard='start2')
                elif message == 'хочу написать заново':
                    context = self.get_context(from_id, message_id)
                    if context[-1]['text'] == phrases['look2']:
                        self.send_message(from_id, phrases['again2'])
                elif message == 'я передумал отправлять':
                    context = self.get_context(from_id, message_id)
                    if context[-1]['text'] in [phrases['look3'], phrases['contacts']]:
                        self.send_message(from_id, phrases['finish3'][2:], keyboard='start2')
                elif event.message['attachments']:
                    context = self.get_context(from_id, message_id)
                    if context[-1]['text'] == phrases['valentine']:
                        if event.message['attachments'][0]['type'] == 'photo':
                            url = sorted(event.message['attachments'][0]['photo']['sizes'],
                                 key=lambda x: x['height']*x['width'], reverse=True)[0]['url']
                            photo = self.upload_photo(url)
                            set_name(from_id, 'photo', photo)
                            set_name(from_id, 'choice', '')
                else:
                    context = self.get_context(from_id, message_id)
                    if context[-1]['text'] == phrases['name']:
                        set_name(from_id, 'name', event.message['text'])
                        valentine = get_valentine(from_id)
                        if 'ready' in valentine.keys() and not valentine['ready']:
                            enum = valentine['enum']
                        else:
                            enum = list(sorted(random.sample(range(15), 5)))
                            set_name(from_id, 'enum', enum)
                            set_name(from_id, 'ready', False)
                        print(enum)
                        self.send_message(from_id, phrases['valentine'], keyboard='choice',
                                          attachment=[valentines[i] for i in range(15) if i in enum])
                    elif context[-1]['text'] == phrases['valentine']:
                        if message in [str(i) for i in range(1, 6)]:
                            set_name(from_id, 'choice', int(message)-1)
                            set_name(from_id, 'photo', '')
                            self.send_message(from_id, phrases['privacy'], keyboard='yes-no')
                    elif context[-1]['text'] == phrases['pseudonym']:
                        set_name(from_id, 'sign', event.message['text'])
                        self.send_message(from_id, phrases['look1'], keyboard='no-yes')
                    elif context[-1]['text'] in [phrases['paragraph'], phrases['again2']]:
                        set_name(from_id, 'paragraph', event.message['text'])
                        self.send_message(from_id, phrases['look2'], keyboard='after_paragraph')
                    elif context[-1]['text'].startswith(phrases['url1']) and \
                            context[-1]['text'].endswith(phrases['url2']):
                        set_name(from_id, 'url', message)
                        self.send_message(from_id, phrases['email1'] +
                                          get_valentine(from_id)['name'] + phrases['email2'], keyboard='skip')
                    elif context[-1]['text'].startswith(phrases['email1']) and \
                            context[-1]['text'].endswith(phrases['email2']):
                        set_name(from_id, 'email', message)
                        self.send_message(from_id, phrases['look3'], keyboard='look3')

    @staticmethod
    def create_keyboard(response):
        keyboard = VkKeyboard(one_time=True)

        if response == 'start':
            keyboard.add_button('Нет, я жду свою валентиночку', color=VkKeyboardColor.SECONDARY)
            keyboard.add_line()
            keyboard.add_button('Да', color=VkKeyboardColor.PRIMARY)

        if response == 'start2':
            keyboard.add_button('Начать', color=VkKeyboardColor.PRIMARY)

        if response == 'start3':
            keyboard.add_button('Нет, я жду свою валентиночку', color=VkKeyboardColor.SECONDARY)
            keyboard.add_line()
            keyboard.add_button('Начать', color=VkKeyboardColor.PRIMARY)

        elif response == 'choice':
            keyboard.add_button('1', color=VkKeyboardColor.PRIMARY)
            keyboard.add_button('2', color=VkKeyboardColor.PRIMARY)
            keyboard.add_button('3', color=VkKeyboardColor.PRIMARY)
            keyboard.add_line()
            keyboard.add_button('4', color=VkKeyboardColor.PRIMARY)
            keyboard.add_button('5', color=VkKeyboardColor.PRIMARY)

        elif response == 'yes-no':
            keyboard.add_button('Да', color=VkKeyboardColor.SECONDARY)
            keyboard.add_button('Нет', color=VkKeyboardColor.PRIMARY)

        elif response == 'no-yes':
            keyboard.add_button('Нет', color=VkKeyboardColor.SECONDARY)
            keyboard.add_button('Да', color=VkKeyboardColor.PRIMARY)

        elif response == 'skip':
            keyboard.add_button('Пропустить', color=VkKeyboardColor.SECONDARY)

        elif response == 'after_paragraph':
            keyboard.add_button('Хочу написать заново', color=VkKeyboardColor.SECONDARY)
            keyboard.add_line()
            keyboard.add_button('Нет', color=VkKeyboardColor.SECONDARY)
            keyboard.add_button('Да', color=VkKeyboardColor.PRIMARY)

        elif response == 'contacts':
            keyboard.add_button('Я передумал отправлять', color=VkKeyboardColor.SECONDARY)
            keyboard.add_line()
            keyboard.add_button('Да', color=VkKeyboardColor.PRIMARY)

        elif response == 'look3':
            keyboard.add_button('Я передумал отправлять', color=VkKeyboardColor.SECONDARY)
            keyboard.add_line()
            keyboard.add_button('Нет', color=VkKeyboardColor.SECONDARY)
            keyboard.add_button('Да', color=VkKeyboardColor.PRIMARY)

        keyboard = keyboard.get_keyboard()
        return keyboard

    def send_message(self, user_id, message, keyboard=None, attachment=None):
        self.bot_api.messages.send(
            random_id=random.getrandbits(32),
            user_id=user_id,
            message=message,
            keyboard=ValentinesDayBot.create_keyboard(keyboard) if keyboard else keyboard,
            attachment=attachment
        )

    def get_context(self, user_id, start_message_id, offset=0, count=2):
        return self.bot_api.method(
            'messages.getHistory',
            {
                'user_id': user_id,
                'start_message_id': start_message_id,
                'offset': offset,
                'count': count
            }
        )['items']

    def get_user(self, url: str):
        if '.com/' in url:
            try:
                user_id = self.bot_api.method(
                    'users.get',
                    {
                        'user_ids': url[url.index('.com/')+5:]
                    }
                )
                return user_id[0]['id'], user_id[0]['first_name']
            except vk_api.exceptions.ApiError:
                return 0, ''
        else:
            return 0, ''

    def tag_user(self, bot_api, user_id, user_name):
        bot_api.method(
            'wall.createComment',
            {
                'owner_id': -self.group_id,
                'post_id': self.post_id,
                'from_group': self.group_id,
                'message': '@id{} ({}), у меня есть валентинка для тебя! '
                           'Скорее напиши "начать" в сообщения группы, чтобы ее получить.'.format(user_id, user_name)
            }
        )

    def upload_photo(self, url):
        upload_url = self.bot_api.photos.getMessagesUploadServer(peer_id=0)['upload_url']
        print(upload_url)
        pic = requests.get(url)
        filename = 'img.jpg' if pic.headers['Content-Type'] == 'image/jpeg' else 'img.png'
        request = requests.post(upload_url, files={'file': (filename, pic.content, pic.headers['Content-Type'])}).json()
        print(request)
        save_pic = self.bot_session.method('photos.saveMessagesPhoto', request)
        print(save_pic)
        pic_attach = 'photo{}_{}'.format(save_pic[0]['owner_id'], save_pic[0]['id'])
        return pic_attach

    def try_to_send_vk(self, valentine):
        message = '{}\n{}'.format(valentine['name'], valentine['paragraph'])
        self.send_message(valentine['to_id'], 'Я принес тебе валентинку!')
        self.send_message(valentine['to_id'], message, attachment=valentines[valentine['choice']])

    def force_send(self, valentine):
        pass
