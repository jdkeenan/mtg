import asyncio
import os

os.environ['KIVY_EVENTLOOP'] = 'asyncio'
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
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
from kivy.uix.floatlayout import FloatLayout
from client import client_connection
from cv_card_reader import cv_card_reader
import random
from table import Table
from picture import Picture
from deck import Deck
from kivy.animation import Animation
import time

class PicturesApp(App):
    conn = client_connection()
    card_database = card_database_creation()
    card_reader = cv_card_reader()
    table = None
    deck = None

    def check_resize(self, instance, x, y):
        print("resize", x, y)
        self.table.bounding_boxes['hand'].set_box(
            [int(x*0.5), int(50)],
            [int(x), int(y*0.2)],
        )
        self.table.bounding_boxes['mana_cards'].set_box(
            [int(0), int(50)],
            [int(x*0.5), int(y*0.2)]
        )
        self.table.bounding_boxes['monsters_cards'].set_box(
            [int(0), int(y*0.2)],
            [int(x), int(y*0.4)]
        )
        self.table.bounding_boxes['attacking_cards'].set_box(
            [int(0), int(y*0.4)],
            [int(x), int(y*0.6)]
        )
        self.current_width = x
        self.current_height = y
        self.table.update_opponent_bounding_boxes()
        self.table.animate_all_cards()
        self.root.canvas.ask_update()
        self.event_loop = []

    def wrapper_create_card(self, name):
        if not isinstance(name, str): name = name.text
        card_id = self.create_card(name)
        self.table.move_card(card_id, 'hand', [Window.width, Window.height])

    def wrapper_send_message(self, name):
        self.conn.writer_tcp(name.text)

    def wrapper_create_card_from_camera(self, event):
        name = self.card_reader.grab_text()
        card_id = self.create_card(name)
        self.table.move_card(card_id, 'hand', [Window.width, Window.height])

    def create_onepone(self, event=None):
        opo = Picture(source='opo.png')
        self.root.add_widget(opo)

    def create_card(self, name, summon_position=None, assigned_id=None):
        # card = card_creation(self.card_database, name)
        return self.table.create_card(name=name, summon_position=None, assigned_id=None)

    def app_func(self):
        async def run_wrapper():
            await self.async_run()
            print('App done')
            self.card_reader.close()
            self.other_task.cancel()

        return asyncio.gather(run_wrapper(), self.client_connection())

    def deck_next_card(self, event):
        if self.deck is None:
            self.deck = Deck()
            for i in self.deck.load_hand():
                self.wrapper_create_card(i)
        else:
           self.wrapper_create_card(self.deck.load_card())

    def build(self):
        self.table = Table(self)
        self.check_resize(None, Window.width, Window.height)
        textinput = TextInput(text='Card Name', multiline=False)
        textinput.bind(on_text_validate=self.wrapper_create_card)
        chatclient = TextInput(text='Chat', multiline=False)
        chatclient.bind(on_text_validate=self.wrapper_send_message)
        button = Button(text='grab card from camera', font_size=14)
        button.bind(on_press=self.wrapper_create_card_from_camera)
        deck = Button(text='grab card from virtual decks', font_size=14)
        deck.bind(on_press=self.deck_next_card)

        layout = BoxLayout(size_hint=(1, None), height=50)
        layout.add_widget(textinput)
        layout.add_widget(chatclient)
        layout.add_widget(button)
        layout.add_widget(deck)
        self.root.add_widget(layout)

        buttonlayout = FloatLayout(size_hint=(None, None), height=50)
        button_1p1 = Button(text="+1/+1", pos_hint={'center_x': 10, 'center_y': 10}, size_hint = (None,None))
        button_1p1.bind(on_press = self.create_onepone)
        buttonlayout.add_widget(button_1p1)

        Window.bind(on_resize=self.check_resize)

    async def client_connection(self):
        try:
            await self.conn.establish_connection()
            await asyncio.sleep(1)

            async def connection():
                await asyncio.sleep(1)
                self.conn.writer_tcp('create_a_room mtg mtg')
                await asyncio.sleep(1)
                self.conn.writer_tcp('join_a_room mtg mtg')
                await asyncio.sleep(1)
                self.conn.writer_tcp('username mtg{}'.format(random.getrandbits(10)))
                await asyncio.sleep(1)
                while True:
                    await asyncio.sleep(5)
                    self.table.broadcast_cards()

            async def card_watcher():
                while True:
                    print(self.event_loop)
                    if len(self.event_loop) > 0 and self.event_loop[0][0] + 0.3 < time.time():
                        # [time.time(), 2, self.parent_object.current_width//2, self.parent_object.current_height//2, self]
                        animation = Animation(pos=(self.event_loop[0][2], self.event_loop[0][3]), t='out_back')
                        animation &= Animation(scale=self.event_loop[0][1], t='in_out_cubic')
                        animation.start(self.event_loop[0][-1])
                        self.event_loop.pop(0)
                    await asyncio.sleep(0.5)

            await asyncio.gather(connection(), card_watcher(), self.conn.reader_tcp(self.incoming_message))

        except asyncio.CancelledError as e:
            pass

    def incoming_message(self, message):
        print(message)
        text = " ".join(message.split(' ')[1:])
        if text.startswith('create_a_card'):
            self.create_card(" ".join(text.split(' ')[1:]))
        if text.startswith('current_cards'):
            self.table.opponent_update(message.split(' ')[0][:-1], " ".join(text.split(' ')[1:]))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(PicturesApp().app_func())
    loop.close()

