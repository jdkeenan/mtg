from kivy.uix.scatter import Scatter
from kivy.uix.boxlayout import BoxLayout
import random
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.animation import Animation
import time

class Picture(Scatter, object):
    def __init__(self, source, parent_object, card, assigned_id=None, opponent=False, tapped=False):
        if assigned_id is None: self.card_id = random.getrandbits(64)
        else: self.card_id = assigned_id
        self.source = source
        self.card = card
        self.name = card.name
        self.parent_object = parent_object
        self.opponent = opponent
        self.tapped = tapped
        self.tap_untap()
        super().__init__()
        self.do_rotation = False
        self.do_scale = False
        self.time = time.time()
        self.previous_small_pos = None
        self.big = False

    def delete(self):
        # import pdb; pdb.set_trace()
        self.parent.remove_widget(self)

    def delete_button(self, event):
        self.parent_object.table.delete(card_id = self.card_id)
        self.popup.dismiss()

    def tap_untap(self):
        self.rotation = 0 if not self.tapped else 90

    # def pre__on_touch_down(self, event):
    def pre__on_touch_down(self, touch):            
        if not self.opponent and self.collide_point(*touch.pos):
            (pos_x, pos_y) = touch.pos
            if touch.is_double_tap:
                if len(self.parent_object.event_loop) > 1: self.parent_object.event_loop.pop(-1)
                self.tapped = not self.tapped
                if not self.opponent: self.parent_object.table.broadcast_cards()
                self.tap_untap()
            if touch.button == 'right':
                OK_button = Button(text='OK')
                self.popup = Popup(content=OK_button, title='delete card?', pos=(self.y, self.x), size_hint=(None,None), size=(200,200))
                OK_button.bind(on_press=self.delete_button)
                self.popup.open()
                return True
        self.time = time.time()

    def post__on_touch_down(self, touch):
        if not self.collide_point(*touch.pos): return

    def pre__on_touch_up(self, touch):
        if not self.collide_point(*touch.pos): return
        
    def post__on_touch_up(self, event):
        if not self.collide_point(*event.pos):
            return
        print(time.time() - self.time)
        if not self.opponent:
            self.parent_object.table.check_position(self.card_id, event.pos)

        if (time.time() - self.time) < 0.25:
            print("running")
            # if not self.big:
            #     print("BIGGLY")
            #     self.big = True
            #     # self.previous_small_pos = [self.x, self.y, self.scale]
            if len(self.parent_object.event_loop) == 0:
                self.parent_object.event_loop.append([time.time(), 2, self.parent_object.current_width//2 , self.parent_object.current_height//2, self])
            # animation = Animation(pos=(self.parent_object.current_width//2, self.parent_object.current_height//2), t='out_back')
            # animation &= Animation(scale=2, t='in_out_cubic')
            # animation.start(self)
            # else:
            #     self.big = False
                # animation = Animation(pos=(self.previous_small_pos[0], self.previous_small_pos[1]), t='out_back')
                # animation &= Animation(scale=self.previous_small_pos[2], t='in_out_cubic')
                # animation.start(self)
        

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
            "tapped": self.tapped
        }
        return parameters