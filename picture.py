from kivy.uix.scatter import Scatter
import random

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

    def pre__on_touch_down(self, event):
        # self.parent_object.table(self.card_id, 'attacking_cards')
        if not self.opponent:
            self.parent_object.table(self.card_id, 'attacking_cards')

    def post__on_touch_down(self, event):
        print("post")

    # def pre__on_touch_up(self, event):
    #     print('up')
    def post__on_touch_up(self, event):
        print(event)
        print("card moved")

    def delete(self):
        self.parent.remove_widget(self)

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