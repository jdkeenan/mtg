import asyncio
import os

os.environ['KIVY_EVENTLOOP'] = 'asyncio'
import kivy
kivy.require('1.0.6')

from glob import glob
from random import randint
from os.path import join, dirname
from kivy.app import App
from kivy.logger import Logger
from kivy.uix.scatter import Scatter
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.properties import StringProperty
from card_search import card_database_creation, card_creation
from kivy.uix.boxlayout import BoxLayout
from client import client_connection
from cv_card_reader import cv_card_reader

class Picture(Scatter, object):
    def __init__(self, source):
        self.source = source
        super().__init__()

    def pre__on_touch_down(self, event):
        print(event)

    def post__on_touch_down(self, event):
        print("post")

    def __getattribute__(self, name):
        if name.startswith('pre__') or name.startswith('post__'): 
            return object.__getattribute__(self, name)
        if hasattr(self, 'pre__' + name) or hasattr(self, 'post__' + name):
            func = object.__getattribute__(self, name)
            def func2(*args, **kwargs):
                if hasattr(self, 'pre__' + name) and object.__getattribute__(self, 'pre__' + name)(*args, **kwargs) is not None: 
                    return
                func(*args, **kwargs)
                if hasattr(self, 'post__' + name) and object.__getattribute__(self, 'post__' + name)(*args, **kwargs): pass
            return func2
        return object.__getattribute__(self, name)


class PicturesApp(App):
    conn = client_connection()
    card_database = card_database_creation()
    card_reader = cv_card_reader()

    def wrapper_create_card(self, name):
        self.create_card(name.text)

    def wrapper_send_message(self, name):
        self.conn.writer_tcp(name.text)

    def wrapper_create_card_from_camera(self, event):
        print(event)
        name = self.card_reader.grab_text()
        print(name)
        self.create_card(name)

    def create_card(self, name):
        card = card_creation(self.card_database, name)
        picture = Picture(source=card.png)
        self.root.add_widget(picture)

    def app_func(self):
        self.other_task = asyncio.ensure_future(self.client_connection())

        async def run_wrapper():
            await self.async_run()
            print('App done')
            self.card_reader.close()
            self.other_task.cancel()

        return asyncio.gather(run_wrapper(), self.other_task)

    def build(self):
        textinput = TextInput(text='Card Name', multiline=False)
        textinput.bind(on_text_validate=self.wrapper_create_card)
        chatclient = TextInput(text='Chat', multiline=False)
        chatclient.bind(on_text_validate=self.wrapper_send_message)
        button = Button(text='grab card from camera', font_size=14)
        button.bind(on_press=self.wrapper_create_card_from_camera)

        layout = BoxLayout(size_hint=(1, None), height=50)
        layout.add_widget(textinput)
        layout.add_widget(chatclient)
        layout.add_widget(button)
        self.root.add_widget(layout)

    async def client_connection(self):
        try:
            await self.conn.establish_connection()
            await self.conn.reader_tcp(self.incoming_message)
        except asyncio.CancelledError as e:
            pass

    def incoming_message(self, message):
        text = " ".join(message.split(' ')[1:])
        if text.startswith('create_a_card'):
            self.create_card(" ".join(text.split(' ')[1:]))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(PicturesApp().app_func())
    loop.close()

