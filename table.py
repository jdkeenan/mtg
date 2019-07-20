import ast
from card_search import card_database_creation, card_creation
from picture import Picture
from kivy.animation import Animation
from kivy.uix.widget import Widget


class LineRectangle(Widget):
    pass

class CardBounding:
    card_height = 557.3770491803278

    def __init__(self, parent, name):
        self.parent = parent
        self.name = name
        self.top_left = None
        self.bottom_right = None
        self.max_scale = 1
        self.max_size = 400
        self.scale = 1 # includes 10% margin
        self.center_x = None
        self.center_y = None
        self.override = False
        self.override_scale = 1
        self.height = None
        self.box = None
        self.set_box([0,0], [1000,1000])

    def set_box(self, top_left, bottom_right):
        self.top_left = top_left
        self.bottom_right = bottom_right
        self.center_x = (bottom_right[0] + top_left[0]) / 2
        self.center_y = (bottom_right[1] + top_left[1]) / 2
        self.height = abs(bottom_right[1] - top_left[1])
        self.max_scale = 1 if self.height > self.card_height else self.height / self.card_height
        if self.box is None:
            self.box = LineRectangle()
            self.parent.root.add_widget(self.box)
        # import pdb; pdb.set_trace()
        self.box.canvas.children[2].rectangle = (*self.top_left, abs(bottom_right[0] - top_left[0]), self.height)
        self.box.canvas.ask_update()
        # self.rect = (*self.top_left, abs(bottom_right[0] - top_left[0]), self.height)

        # self.box.label.text = self.name

    def card_positions(self, number_cards, quick = False):
        pos = [int(self.center_x - self.width * (number_cards//2 + (0.5*((number_cards+1) % 2)) + (number_cards % 2)) + self.width * (i+1)) for i in range(number_cards)]
        if pos[0] - self.width // 2 < self.top_left[0] or pos[-1] + self.width // 2 > self.bottom_right[0]:
            if quick: return False
            self.scale *= 0.85
            return self.card_positions(number_cards)
        if quick: return True
        # check
        self.override = True
        self.override_scale = self.scale * 1.15
        if self.override_scale > self.max_scale: self.override_scale = self.max_scale
        if self.card_positions(number_cards, quick = True):
            self.scale = self.override_scale
        self.override = False
        return pos

    def point_in_box(self, pos):
        if (pos[0] > self.top_left[0] and pos[0] < self.bottom_right[0] and 
            pos[1] > self.top_left[1] and pos[1] < self.bottom_right[1]): return True
        return False

    @property
    def width(self):
        if self.override: return self.override_scale * self.max_size
        return self.scale * self.max_size


class Table:
    def __init__(self, parent, opponent=False):
        self.parent = parent
        self.opponent = opponent
        self.monsters_cards = []
        self.attacking_cards = []
        self.mana_cards = []
        self.hand = []
        self.opponents = {}
        self.picture_lookup = {}
        self.bounding_boxes = {
            "attacking_cards": CardBounding(self.parent, "attacking_cards"), 
            "mana_cards": CardBounding(self.parent, "mana_cards"),
            "monsters_cards": CardBounding(self.parent, "monsters_cards"),
            "hand": CardBounding(self.parent, "hand")
        }

    def check_position(self, card_id, pos):
        # print(pos, pos[0], pos[1])
        for target in self.bounding_boxes.keys():
            # print(target, self.bounding_boxes[target].point_in_box(pos), self.bounding_boxes[target].top_left, self.bounding_boxes[target].bottom_right)
            if self.bounding_boxes[target].point_in_box(pos):
                self.move_card(card_id, target, pos)
                break
        else:
            self.move_card(card_id, 'hand', pos)

    def broadcast_cards(self):
        # broadcast card is played to position
        # change this to broadcast the entire table excluding opponents
        if self.opponent: return
        current_payload = self.get_parameters()
        self.parent.conn.writer_tcp("current_cards {}".format(current_payload))

    # logging
    def get_parameters(self) -> dict:
        parameters = {
            method_name[4:]: getattr(self, method_name)() for method_name in dir(self) if method_name.startswith('_get')
        }
        return parameters

    def _getmonsters_cards(self):
        return self.establish_cards(self.monsters_cards)

    def _getattacking_cards(self):
        return self.establish_cards(self.attacking_cards)

    def _getmana_cards(self):
        return self.establish_cards(self.mana_cards)

    def _gethand(self):
        return self.establish_cards(self.mana_cards)

    def establish_cards(self, parameter):
        cards = []
        for i in parameter:
            cards.append(self.picture_lookup[i].get_parameters())
        return cards

    def load(self, payload):
        try:
            payload = ast.literal_eval(payload)
        except:
            return
        # find cards that need to be deleted or added
        payload_ids = []
        for i in payload.keys():
            if i == 'hand': continue
            for card in payload[i]:
                if card['card_id'] not in self.picture_lookup:
                    self.create_card(name=card['name'], summon_position=i, assigned_id=card['card_id'], tapped=card['tapped'])
                elif card['card_id'] not in getattr(self, i):
                    self.move_card(card['card_id'], i, [0,0])
                self.picture_lookup[card['card_id']].tapped = card['tapped']
                self.picture_lookup[card['card_id']].tap_untap()
                payload_ids.append(card['card_id'])
        for i in list(self.picture_lookup.keys()):
            if i not in payload_ids:
                self.delete(card_id=i)
        # animate all cards
        self.animate_all_cards()
    
    def create_card(self, name, summon_position=None, assigned_id=None, tapped=None):
        card = card_creation(self.parent.card_database, name)
        picture = Picture(source=card.normal, parent_object=self.parent,
                          card=card, assigned_id=assigned_id, opponent=self.opponent, tapped=tapped)
        self.parent.root.add_widget(picture)
        self.picture_lookup[picture.card_id] = picture
        if summon_position is not None:
            getattr(self, summon_position).append(picture.card_id)
        return picture.card_id


    def delete(self, payload=None, card_id=None, quick_return=False):
        if payload is not None: card_id = payload['card_id']
        # delete from the group
        lookup = self.get_parameters()
        for val in lookup.keys():
            if card_id in getattr(self, val):
                getattr(self, val).remove(card_id)
                self.animate_cards(val)
                break
        if quick_return: return
        # delete from lookup
        self.broadcast_cards()
        if card_id in self.picture_lookup:
            self.picture_lookup[card_id].delete()
            del self.picture_lookup[card_id]
            return True
        for opponent in self.opponents.keys():
            if self.opponents[opponent].delete(card_id=card_id): break

    def animate_cards(self, destination):
        if len(getattr(self, destination)) == 0: return
        positions = self.bounding_boxes[destination].card_positions(len(getattr(self, destination)))
        for ind, i in enumerate(getattr(self, destination)):
            animation = Animation(pos=(positions[ind]-self.bounding_boxes[destination].width//2, self.bounding_boxes[destination].center_y-self.bounding_boxes[destination].height//2), t='out_back')
            if self.picture_lookup[i].scale != self.bounding_boxes[destination].scale:
                animation &= Animation(scale=self.bounding_boxes[destination].scale, t='in_out_cubic')
            animation.start(self.picture_lookup[i])

    def animate_all_cards(self):
        for val in self.get_parameters().keys():
            self.animate_cards(val)

    def move_card(self, card_id, destination, cur_pos): #cur_pos [x, y]
        if card_id in getattr(self, destination): 
            # cards in stack
            number_cards = len(getattr(self, destination))
            if number_cards == 0: 
                return
            positions = self.bounding_boxes[destination].card_positions(number_cards)
            print(positions, cur_pos, cur_pos[0])
            card_found = False
            for ind, i in enumerate(positions):
                if getattr(self, destination)[ind] == card_id: card_found = True
                if cur_pos[0] < i + self.bounding_boxes[destination].width // 2:
                    # insert card at this position
                    getattr(self, destination).insert(ind, card_id)
                    if card_found: 
                        getattr(self, destination).remove(card_id)
                    else: 
                        index = getattr(self, destination)[ind+1:].index(card_id)
                        getattr(self, destination).pop(index+ind+1)
                    break
            else:
                getattr(self, destination).append(card_id)
                getattr(self, destination).remove(card_id)
            self.animate_cards(destination)
            # move cards to centers
            # should we reorder cards
            # cards do not change size
            return
        self.delete(card_id=card_id, quick_return=True)
        getattr(self, destination).append(card_id)
        self.animate_cards(destination)
        self.broadcast_cards()

    # opponent updates
    def opponent_update(self, opponent, payload):
        if opponent not in self.opponents:
            self.opponents[opponent] = Table(self.parent, opponent=True)
            self.update_opponent_bounding_boxes()
        self.opponents[opponent].load(payload)

    def update_opponent_bounding_boxes(self):
        for ind, opponent in enumerate(self.opponents.keys()):
            self.opponents[opponent].create_opponent_bounds(ind, len(self.opponents))

    def create_opponent_bounds(self, ind, number_of_opponents):
        x = self.parent.current_width
        y = self.parent.current_height
        x = x // number_of_opponents
        offset = int(ind*x)
        self.bounding_boxes['hand'].set_box(
            [int(x*0.5+offset), int(y*0.9)],
            [int(x+offset), int(y*1.0)]
        )
        self.bounding_boxes['mana_cards'].set_box(
            [int(0+offset), int(y*0.9)],
            [int(x*0.5+offset), int(y*1.0)]
        )
        self.bounding_boxes['monsters_cards'].set_box(
            [int(0+offset), int(y*0.75)],
            [int(x+offset), int(y*0.9)]
        )
        self.bounding_boxes['attacking_cards'].set_box(
            [int(0+offset), int(y*0.6)],
            [int(x+offset), int(y*0.75)]
        )
        self.animate_all_cards()

    def remove_opponent(self,  name):
        if name in opponents: del opponents[name]
