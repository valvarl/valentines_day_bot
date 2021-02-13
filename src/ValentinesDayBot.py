# ! /usr/bin/env python
# -*- coding: utf-8 -*-

import vk_api
import vk_api.exceptions
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import random
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from src.Firebase import *
from datetime import datetime, timedelta
from time import sleep

with open('src/phrases.json', encoding='utf8') as inf:
    phrases = json.load(inf)

with open('src/valentines.json', encoding='utf8') as inf:
    valentines = json.load(inf)

DAY_X = 14
HOUR_X = 22


class ValentinesDayBot:
    def __init__(self, group_token, group_id, post_id, email, password, st1_start, st2_start):
        self.group_id = group_id
        self.post_id = post_id
        self.email = email
        self.password = password
        self.st1_start = st1_start
        self.st2_start = st2_start

        self.bot_session = vk_api.VkApi(token=group_token)
        self.bot_api = self.bot_session.get_api()
        # print('ready')

    def start(self):
        while True:
            longpoll = VkBotLongPoll(self.bot_session, self.group_id)
            try:
                for event in longpoll.listen():
                    if event.type == VkBotEventType.MESSAGE_NEW and event.from_user:
                        # print(event.message)
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
                            if context[-1]['from_id'] != -self.group_id:
                                continue
                            if context[-1]['text'] == phrases['greeting'] and get_valentine(from_id)['remain'] > 0:
                                self.send_message(from_id, phrases['name'])
                            elif context[-1]['text'] == phrases['privacy']:
                                set_name(from_id, 'sign', '')
                                set_name(from_id, 'paragraph', '')
                                self.send_vk(from_id, get_valentine(from_id))
                                self.send_message(from_id, phrases['look1'], keyboard='no-yes')
                            elif context[-1]['text'] == phrases['look1']:
                                self.send_message(from_id, phrases['paragraph'], keyboard='skip')
                            elif context[-1]['text'] == phrases['look2']:
                                self.send_message(from_id, phrases['url1'] +
                                                  get_valentine(from_id)['name'] + phrases['url2'], keyboard='skip')
                            elif context[-1]['text'] == phrases['contacts']:
                                self.send_message(from_id, phrases['url1'] +
                                                  get_valentine(from_id)['name'] + phrases['url2'], keyboard='skip')
                            elif context[-1]['text'].endswith(phrases['look3']):
                                valentine = get_valentine(from_id)
                                remain = valentine['remain'] - 1
                                set_name(from_id, 'remain', remain)
                                to_id, to_name = self.get_user(valentine['url'])
                                valentine, storage_link = storage_valentine(from_id, to_id, to_name)
                                user_in_system = to_id in users_in_system()
                                now = datetime.utcnow() + timedelta(hours=3)
                                if now >= datetime(2021, 2, DAY_X, HOUR_X):
                                    if self.force_send(valentine['to_id'], valentine):
                                        mark_sent(storage_link)
                                elif to_id:
                                    if now.day >= DAY_X:
                                        if user_in_system:
                                            if self.send_vk(to_id, valentine):
                                                mark_sent(storage_link)
                                                self.send_message(valentine['to_id'], phrases['received'],
                                                                  keyboard='start2')
                                        else:
                                            self.tag_user(to_id, to_name)
                                    elif not user_in_system:
                                        self.tag_user(to_id, to_name)
                                    else:
                                        self.send_message(to_id, phrases['another_one'])
                                set_name(from_id, 'ready', True)
                                if remain > 0:
                                    self.send_message(from_id, phrases['finish1'] + phrases['finish2'] +
                                                      ['одну', 'две'][remain - 1] + phrases['finish3'],
                                                      keyboard='start3')
                                else:
                                    self.send_message(from_id, phrases['finish1'] + phrases['finish4'])
                        elif message == 'нет':
                            context = self.get_context(from_id, message_id)
                            if context[-1]['from_id'] != -self.group_id:
                                continue
                            if context[-1]['text'] == phrases['privacy']:
                                self.send_message(from_id, phrases['pseudonym'])
                            elif context[-1]['text'] == phrases['look1'] and get_valentine(from_id)['remain'] > 0:
                                self.send_message(from_id, phrases['finish3'][2:], keyboard='start2')
                            elif context[-1]['text'] == phrases['look2']:
                                set_name(from_id, 'paragraph', '')
                                self.send_message(from_id, phrases['url1'] +
                                                  get_valentine(from_id)['name'] + phrases['url2'], keyboard='skip')
                            elif context[-1]['text'].endswith(phrases['look3']):
                                self.send_message(from_id, phrases['url1'] +
                                                  get_valentine(from_id)['name'] + phrases['url2'], keyboard='skip')
                        elif message == 'пропустить':
                            context = self.get_context(from_id, message_id)
                            if context[-1]['from_id'] != -self.group_id:
                                continue
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
                                    self.send_message(from_id, 'vk: {}\nemail: {}\n\n'.
                                                      format(valentine['url'], valentine['email']) + phrases['look3'],
                                                      keyboard='look3')
                                else:
                                    self.send_message(from_id, phrases['contacts'], keyboard='contacts')
                        elif message == 'нет, я жду свою валентиночку':
                            context = self.get_context(from_id, message_id)
                            if context[-1]['from_id'] == -self.group_id and context[-1]['text'] == phrases['greeting'] or \
                                    context[-1]['text'].endswith(phrases['finish3'][2:]):
                                valentine = expect_valentine(from_id)
                                if valentine:
                                    now = datetime.utcnow() + timedelta(hours=3)
                                    if now.day >= DAY_X:
                                        for v in valentine:
                                            self.send_vk(from_id, v)
                                            mark_sent(v['storage_url'])
                                        self.send_message(from_id, phrases['received'], keyboard='start2')
                                    else:
                                        self.send_message(from_id, phrases['not_send'], keyboard='start2')
                                else:
                                    self.send_message(from_id, phrases['not_expect'], keyboard='start2')
                        elif message == 'хочу написать заново':
                            context = self.get_context(from_id, message_id)
                            if context[-1]['from_id'] == -self.group_id and context[-1]['text'] == phrases['look2']:
                                self.send_message(from_id, phrases['again2'])
                        elif message == 'я передумал отправлять':
                            context = self.get_context(from_id, message_id)
                            if context[-1]['from_id'] == -self.group_id and (context[-1]['text'] == phrases['contacts']
                                                                             or context[-1]['text'].endswith(
                                        phrases['look3'])):
                                self.send_message(from_id, phrases['finish3'][2:], keyboard='start2')
                        elif event.message['attachments'] and event.message['attachments'][0]['type'] == 'photo':
                            context = self.get_context(from_id, message_id)
                            if context[-1]['from_id'] == -self.group_id and context[-1]['text'] == phrases['valentine']:
                                url = sorted(event.message['attachments'][0]['photo']['sizes'],
                                             key=lambda x: x['height'] * x['width'], reverse=True)[0]['url']
                                photo = self.upload_photo(url)
                                set_name(from_id, 'photo_url', url)
                                set_name(from_id, 'photo', photo)
                                set_name(from_id, 'choice', '')
                                self.send_message(from_id, phrases['privacy'], keyboard='yes-no')
                        elif message == self.st1_start:
                            self.send_message(from_id, "Начинаю рассылку валентинок по вк.")
                            self.broadcast(self.send_vk)
                            self.send_message(from_id, "Рассылка завершена.")
                        elif message == self.st2_start:
                            self.send_message(from_id, "Начинаю рассылку оставшихся валентинок.")
                            self.broadcast(self.force_send)
                            self.send_message(from_id, "Рассылка завершена.")
                        else:
                            context = self.get_context(from_id, message_id)
                            if context[-1]['from_id'] != -self.group_id:
                                continue
                            if context[-1]['text'] == phrases['name']:
                                set_name(from_id, 'name', event.message['text'])
                                valentine = get_valentine(from_id)
                                if 'ready' not in valentine.keys() or 'ready' in valentine.keys() and valentine[
                                    'ready']:
                                    enum = list(sorted(random.sample(range(15), 5)))
                                    set_name(from_id, 'enum', enum)
                                    set_name(from_id, 'ready', False)
                                else:
                                    enum = valentine['enum']
                                # print(enum)
                                self.send_message(from_id, phrases['valentine'], keyboard='choice',
                                                  attachment=[valentines[i] for i in range(15) if i in enum])
                            elif context[-1]['text'] == phrases['valentine']:
                                if message in [str(i) for i in range(1, 6)]:
                                    set_name(from_id, 'choice', int(message) - 1)
                                    set_name(from_id, 'photo', '')
                                    self.send_message(from_id, phrases['privacy'], keyboard='yes-no')
                            elif context[-1]['text'] == phrases['pseudonym']:
                                set_name(from_id, 'sign', event.message['text'])
                                set_name(from_id, 'paragraph', '')
                                self.send_vk(from_id, get_valentine(from_id))
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
                                valentine = get_valentine(from_id)
                                self.send_message(from_id, 'vk: {}\nemail: {}\n\n'.
                                                  format(valentine['url'], valentine['email']) + phrases['look3'],
                                                  keyboard='look3')
            except requests.exceptions.ReadTimeout:
                sleep(2)

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
        return self.bot_api.messages.getHistory(
            user_id=user_id,
            start_message_id=start_message_id,
            offset=offset,
            count=count
        )['items']

    def get_user(self, url: str):
        if '.com/' in url:
            try:
                user_id = self.bot_api.users.get(
                    user_ids=url[url.index('.com/') + 5:]
                )
                return user_id[0]['id'], user_id[0]['first_name']
            except vk_api.exceptions.ApiError:
                return 0, ''
        else:
            return 0, ''

    def tag_user(self, user_id, user_name):
        self.bot_api.wall.createComment(
            owner_id=-self.group_id,
            post_id=self.post_id,
            from_group=self.group_id,
            message='@id{} ({}), у меня есть валентинка для тебя! '
                    'Скорее напиши "начать" в сообщения группы, чтобы ее получить.'.format(user_id, user_name)
        )

    def upload_photo(self, url):
        upload_url = self.bot_api.photos.getMessagesUploadServer(peer_id=0)['upload_url']
        # print(upload_url)
        pic = requests.get(url)
        filename = 'img.jpg' if pic.headers['Content-Type'] == 'image/jpeg' else 'img.png'
        request = requests.post(upload_url, files={'file': (filename, pic.content, pic.headers['Content-Type'])}).json()
        # print(request)
        save_pic = self.bot_session.method('photos.saveMessagesPhoto', request)
        # print(save_pic)
        pic_attach = 'photo{}_{}'.format(save_pic[0]['owner_id'], save_pic[0]['id'])
        return pic_attach

    def send_vk(self, user_id, valentine):
        try:
            sign = ' от ' + valentine['sign'] if valentine['sign'] else ''
            paragraph = '\n\n' + valentine['paragraph'] if valentine['paragraph'] else ''
            message = '{}, это тебе{}!{}'.format(valentine['name'], sign, paragraph)
            attachment = valentine['photo'] if valentine['photo'] else valentines[
                valentine['enum'][valentine['choice']]]
            self.send_message(user_id, message, attachment=attachment)
            return True
        except Exception:
            return False

    def force_send(self, user_id, valentine):
        if user_id in users_in_system() and self.send_vk(user_id, valentine):
            return True
        elif valentine['email']:
            message = MIMEMultipart()
            message['From'] = self.email
            message['To'] = valentine['email']
            message['Subject'] = 'Валентинка 😊'
            sign = (' ' if valentine['sign'].lower().startswith('от') else ' от ') + valentine['sign'] if valentine[
                'sign'] else ''
            paragraph = '\n\n' + valentine['paragraph'] if valentine['paragraph'] else ''
            msg = '{}, это тебе{}!{}'.format(valentine['name'], sign, paragraph)
            message.attach(MIMEText(msg, 'plain'))

            if valentine['photo'] == '':
                attach_file_name = 'valentine%d.mp4' % valentine['choice']
                attach_file = open('valentines/' + attach_file_name, 'rb')
            else:
                pic = requests.get(valentine['photo_url'])
                attach_file_name = 'img.jpg' if pic.headers['Content-Type'] == 'image/jpeg' else 'img.png'
                with open('valentines/' + attach_file_name, 'wb') as fd:
                    for chunk in pic.iter_content(128):
                        fd.write(chunk)
                attach_file = open('valentines/' + attach_file_name, 'rb')

            payload = MIMEBase('application', 'octet-stream')
            payload.set_payload(attach_file.read())
            encoders.encode_base64(payload)
            payload.add_header('Content-Disposition', 'attachment', filename=attach_file_name)
            message.attach(payload)

            try:
                session = smtplib.SMTP_SSL('smtp.mail.ru', 465)
                session.login(self.email, self.password)
                text = message.as_string()
                session.sendmail(self.email, valentine['email'], text)
                session.quit()
                # print('Mail Sent')
                return True
            except Exception:
                # print('Mail not Sent')
                return False

        else:
            archive(valentine)
            return False

    @staticmethod
    def broadcast(func):
        val = get_valentines()
        if val:
            for v in [v for v in val.keys() if val[v]['to_id'] and not val[v]['sent']]:
                if func(val[v]['to_id'], val[v]):
                    mark_sent(v)
