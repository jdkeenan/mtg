from kivy.uix.scatter import Scatter
from kivy.uix.boxlayout import BoxLayout
import random
from kivy.uix.popup import Popup
from kivy.uix.button import Button

class Picture(Scatter, object):
    def __init__(self, source, parent_object, card, assigned_id=None, opponent=False):
        if assigned_id is None: self.card_id = random.getrandbits(64)
        else: self.card_id = assigned_id
        self.source = source
        self.card = card
        self.name = card.name
        self.cpos = [None, None]
        self.parent_object = parent_object
        self.opponent = opponent
        super().__init__()

    def delete(self, event):
        try:
            self.parent.remove_widget(self)
        except:
            pass

    # def pre__on_touch_down(self, event):
    def pre__on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            (pos_x, pos_y) = touch.pos
            if touch.is_double_tap:
                self.rotation = 0 if self.rotation == 90 else 90
            if touch.button == 'right':
                OK_button = Button(text='OK')
                popup = Popup(content=OK_button, title='delete card?', pos=(pos_x, pos_y), size_hint=(None,None), size=(200,200))
                OK_button.bind(on_press=self.delete)
                popup.open()
                # return True

    def post__on_touch_down(self, event):
        if not self.collide_point(*event.pos):
            return
        print("post")

    # def pre__on_touch_up(self, event):
    #     print('up')
    def post__on_touch_up(self, event):
        if not self.collide_point(*event.pos):
            return
        if not self.opponent:
            self.parent_object.table.move_card(self.card_id, 'attacking_cards', event.pos)
        print(event)
        print("card moved")

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

    def get_parameters(self) -> dict:
        parameters = {
            "card_id": self.card_id,
            "name": self.name,
        }
        return parameters