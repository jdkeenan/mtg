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
from kivy.core.window import Window
from kivy.properties import StringProperty
from card_search import card_database_creation, card_creation
from kivy.uix.boxlayout import BoxLayout
from client import client_connection
from cv_card_reader import cv_card_reader
import random
from table import Table
from picture import Picture

class PicturesApp(App):
    conn = client_connection()
    card_database = card_database_creation()
    card_reader = cv_card_reader()
    table = None

    def check_resize(self, instance, x, y):
        print("resize", x, y)

    def wrapper_create_card(self, name):
        self.create_card(name.text)

    def wrapper_send_message(self, name):
        self.conn.writer_tcp(name.text)

    def wrapper_create_card_from_camera(self, event):
        print(event)
        name = self.card_reader.grab_text()
        print(name)
        self.create_card(name)

    def create_card(self, name, summon_position=None, assigned_id=None):
        # card = card_creation(self.card_database, name)
        self.table.create_card(name=name, summon_position=None, assigned_id=None)

    def app_func(self):
        self.other_task = asyncio.ensure_future(self.client_connection())

        async def run_wrapper():
            await self.async_run()
            print('App done')
            self.card_reader.close()
            self.other_task.cancel()

        return asyncio.gather(run_wrapper(), self.other_task)

    def build(self):
        self.table = Table(self)
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
        Window.bind(on_resize=self.check_resize)

    async def client_connection(self):
        try:
            await self.conn.establish_connection()
            self.conn.writer_tcp('join_a_room mtg mtg')
            await asyncio.sleep(1)
            self.conn.writer_tcp('username mtg_test')
            await self.conn.reader_tcp(self.incoming_message)
        except asyncio.CancelledError as e:
            pass

    def incoming_message(self, message):
        text = " ".join(message.split(' ')[1:])
        if text.startswith('create_a_card'):
            self.create_card(" ".join(text.split(' ')[1:]))
        if text.startswith('current_cards'):
            self.table.opponent_update(message.split(' ')[0][:-1], " ".join(text.split(' ')[1:]))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(PicturesApp().app_func())
    loop.close()

