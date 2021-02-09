# ! /usr/bin/env python
# -*- coding: utf-8 -*-

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import random
from src.Firebase import *


class ValentinesDayBot:
    def __init__(self, group_token, group_id):
        self.group_id = group_id
        with open('src/phrases.json', encoding='utf8') as inf:
            self.phrases = json.load(inf)['phrases']

        self.bot_session = vk_api.VkApi(token=group_token)
        self.bot_api = self.bot_session.get_api()

    def start(self):
        longpoll = VkBotLongPoll(self.bot_session, self.group_id)
        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW and event.from_user:
                from_id = event.message['from_id']
                message_id = event.message['id']
                message = event.message['text'].lower()
                if message in ['начать', 'start']:
                    if event.message['conversation_message_id'] != 1:
                        context = self.get_context(self.bot_session, from_id, message_id)
                        if context[-1]['text'] == self.phrases['not_send']:
                            self.send_message(self.bot_api, from_id, self.phrases['name'])
                        else:
                            self.send_message(self.bot_api, from_id, self.phrases['greeting'], keyboard='start')
                    else:
                        self.send_message(self.bot_api, from_id, self.phrases['greeting'], keyboard='start')
                elif message == 'да':
                    context = self.get_context(self.bot_session, from_id, message_id)
                    if context[-1]['text'] == self.phrases['greeting']:
                        new_valentine(from_id)
                        self.send_message(self.bot_api, from_id, self.phrases['name'])
                    elif context[-1]['text'] == self.phrases['privacy']:
                        self.send_message(self.bot_api, from_id, self.phrases['look1'], keyboard='no-yes')
                    elif context[-1]['text'] == self.phrases['look1']:
                        self.send_message(self.bot_api, from_id, self.phrases['paragraph'], keyboard='skip')
                    elif context[-1]['text'] == self.phrases['look2']:
                        self.send_message(self.bot_api, from_id, self.phrases['url1'] + self.phrases['url2'], keyboard='skip')
                    elif context[-1]['text'] == self.phrases['look3']:
                        self.send_message(self.bot_api, from_id, self.phrases['finish1'])
                elif message == 'нет':
                    context = self.get_context(self.bot_session, from_id, message_id)
                    if context[-1]['text'] == self.phrases['privacy']:
                        self.send_message(self.bot_api, from_id, self.phrases['pseudonym'])
                    elif context[-1]['text'] == self.phrases['look1']:
                        self.send_message(self.bot_api, from_id, self.phrases['again1'] + self.phrases['name'])
                    elif context[-1]['text'] == self.phrases['look2']:
                        self.send_message(self.bot_api, from_id, self.phrases['url1'] + self.phrases['url2'], keyboard='skip')
                elif message == 'пропустить':
                    context = self.get_context(self.bot_session, from_id, message_id)
                    if context[-1]['text'] in [self.phrases['paragraph'], self.phrases['again2']]:
                        self.send_message(self.bot_api, from_id, self.phrases['url1'] + self.phrases['url2'], keyboard='skip')
                    elif context[-1]['text'].startswith(self.phrases['url1']) and \
                            context[-1]['text'].endswith(self.phrases['url2']):
                        self.send_message(self.bot_api, from_id, self.phrases['email1'] + self.phrases['email2'], keyboard='skip')
                    elif context[-1]['text'].startswith(self.phrases['email1']) and \
                            context[-1]['text'].endswith(self.phrases['email2']):
                        self.send_message(self.bot_api, from_id, self.phrases['look3'])
                elif message == 'нет, я жду свою валентиночку':
                    self.send_message(self.bot_api, from_id, self.phrases['not_send'], keyboard='start2')
                elif message == 'хочу написать заново':
                    context = self.get_context(self.bot_session, from_id, message_id)
                    if context[-1]['text'] == self.phrases['look2']:
                        self.send_message(self.bot_api, from_id, self.phrases['again2'])
                else:
                    context = self.get_context(self.bot_session, from_id, message_id)
                    if context[-1]['text'] in [self.phrases['name'], self.phrases['again1'] + self.phrases['name']]:
                        self.send_message(self.bot_api, from_id, self.phrases['valentine'], keyboard='choice')
                    elif context[-1]['text'] == self.phrases['valentine']:
                        self.send_message(self.bot_api, from_id, self.phrases['privacy'], keyboard='yes-no')
                    elif context[-1]['text'] == self.phrases['pseudonym']:
                        self.send_message(self.bot_api, from_id, self.phrases['look1'], keyboard='no-yes')
                    elif context[-1]['text'] in [self.phrases['paragraph'], self.phrases['again2']]:
                        self.send_message(self.bot_api, from_id, self.phrases['look2'], keyboard='after_paragraph')
                    elif context[-1]['text'].startswith(self.phrases['url1']) and \
                            context[-1]['text'].endswith(self.phrases['url2']):
                        self.send_message(self.bot_api, from_id, self.phrases['email1'] + self.phrases['email2'], keyboard='skip')
                    elif context[-1]['text'].startswith(self.phrases['email1']) and \
                            context[-1]['text'].endswith(self.phrases['email2']):
                        self.send_message(self.bot_api, from_id, self.phrases['look3'])

    @staticmethod
    def create_keyboard(response):
        keyboard = VkKeyboard(one_time=True)

        if response == 'start':
            keyboard.add_button('Нет, я жду свою валентиночку', color=VkKeyboardColor.SECONDARY)
            keyboard.add_button('Да', color=VkKeyboardColor.PRIMARY)

        if response == 'start2':
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
            keyboard.add_button('Нет', color=VkKeyboardColor.SECONDARY)
            keyboard.add_button('Да', color=VkKeyboardColor.PRIMARY)

        keyboard = keyboard.get_keyboard()
        return keyboard


    @staticmethod
    def send_message(bot_api, user_id, message, keyboard=None, attachment=None):
        bot_api.messages.send(
            random_id=random.getrandbits(32),
            user_id=user_id,
            message=message,
            keyboard=ValentinesDayBot.create_keyboard(keyboard) if keyboard else keyboard,
            attachment=attachment
        )

    @staticmethod
    def get_context(bot_api, user_id, start_message_id, offset=0, count=2):
        return bot_api.method(
            'messages.getHistory',
            {
                'user_id': user_id,
                'start_message_id': start_message_id,
                'offset': offset,
                'count': count
            }
        )['items']
