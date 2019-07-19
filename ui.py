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
from kivy.uix.textinput import TextInput
from kivy.properties import StringProperty
from card_search import card_database_creation, card_creation
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import DragBehavior
from kivy.uix.scatter import Scatter
from kivy.uix.label import Label
from kivy.input.shape import ShapeRect
from kivy.uix.label import Label
from kivy.uix.behaviors import DragBehavior

from client import client_connection
from kivy.uix.button import Button
from kivy.uix.bubble import Bubble



class Picture(Scatter, object):

    def __init__(self, source):
        self.source = source
        super().__init__()

    def pre__on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.is_double_tap:
                self.rotation = 0 if self.rotation == 90 else 90
            if touch.button == 'right':
                self.parent.remove_widget(self)



    # def post__on_touch_down(self, event):
    #     if self.collide_point(*touch.pos):
    #         self.scale = 1.5
    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.scale = 1.0

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

class DragLabel(DragBehavior, Label):
        pass

class PicturesApp(App):
    conn = client_connection()
    card_database = card_database_creation()

    def wrapper_create_card(self, name):
        self.create_card(name.text)

    def wrapper_send_message(self, name):
        self.conn.writer_tcp(name.text)

    def create_card(self, name):
        card = card_creation(self.card_database, name)
        picture = Picture(source=card.png)
        serlf.root.add_widget(picture)

    def create_onepone(self, event=None):
        opo = Label(text='Hello world', font_size='20sp')

        # opo = Picture(source='opo.png')
        self.root.add_widget(opo)

    def create_npn(self, name):
        print(name)

    def remove_card(self, instance):
        self.root.remove_widget(self)

    def app_func(self):
        self.other_task = asyncio.ensure_future(self.client_connection())

        async def run_wrapper():
            await self.async_run()
            print('App done')
            self.other_task.cancel()

        return asyncio.gather(run_wrapper(), self.other_task)

    def build(self):
        textinput = TextInput(text='Card Name', multiline=False)
        textinput.bind(on_text_validate=self.wrapper_create_card)
        chatclient = TextInput(text='Chat', multiline=False)
        chatclient.bind(on_text_validate=self.wrapper_send_message)
        
        layout = BoxLayout(size_hint=(1, None), height=50)
        layout.add_widget(textinput)
        layout.add_widget(chatclient)
        self.root.add_widget(layout)

        buttonlayout = FloatLayout(size_hint=(None, None), height=50)
        button_1p1 = Button(text="+1/+1", pos_hint={'center_x': 0.5, 'center_y': 22}, size_hint = (1, 1))
        button_1p1.bind(on_press = self.create_onepone)
        buttonlayout.add_widget(button_1p1)
        
        # npn_input = TextInput(text='0/0', multiline=False)
        # npn_button = Button(text="+n/+n", pos_hint={'center_x': 0.5, 'center_y': 20}, size_hint = (1, 1))
        # npn_input.bind(on_text_validate=create_npn)
        
        self.root.add_widget(buttonlayout)



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


