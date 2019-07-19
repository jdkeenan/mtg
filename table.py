import ast
from card_search import card_database_creation, card_creation
from picture import Picture
from kivy.animation import Animation

class CardBounding:
    def __init__(self):
        self.top_left = None
        self.bottom_right = None
        self.max_size = 400
        self.scale = 1 # includes 10% margin
        self.center_x = None
        self.center_y = None
        self.override = False
        self.override_scale = 1
        self.set_box([0,0], [1000,1000])

    def set_box(self, top_left, bottom_right):
        self.top_left = top_left
        self.bottom_right = bottom_right
        self.center_x = (bottom_right[0] + top_left[0]) / 2
        self.center_y = (bottom_right[1] + top_left[1]) / 2

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
        if self.override_scale > 1: self.override_scale = 1
        if self.card_positions(number_cards, quick = True):
            self.scale = self.override_scale
        self.override = False
        return pos

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
            "attacking_cards": CardBounding(), 
            "mana_cards": CardBounding(),
            "monsters_cards": CardBounding()
        }

    def check_position(self, pos): 
        # returns a position closest on the playing field:
        pass

    def broadcast_cards(self):
        # broadcast card is played to position
        # change this to broadcast the entire table excluding opponents
        self.parent.conn.writer_tcp("current_cards {}".format(self.get_parameters()))

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

    def establish_cards(self, parameter):
        cards = []
        for i in parameter:
            cards.append(self.picture_lookup[i].get_parameters())
        return cards

    def load(self, payload):
        payload = ast.literal_eval(payload)
        for i in payload.keys():
            if payload[i] != getattr(self, i):
                current_packet = getattr(self, i).copy()
                for card in payload[i]:
                    if card['card_id'] in current_packet:
                        current_packet.remove(card['card_id'])
                    else:
                        self.create_card(name=card['name'], summon_position=i, assigned_id=card['card_id'])
                for card in current_packet:
                    self.delete(card_id=card)
    
    def create_card(self, name, summon_position=None, assigned_id=None):
        card = card_creation(self.parent.card_database, name)
        picture = Picture(source=card.png, parent_object=self.parent,
                          card=card, assigned_id=assigned_id, opponent=self.opponent)
        self.parent.root.add_widget(picture)
        self.picture_lookup[picture.card_id] = picture
        if summon_position is not None:
            getattr(self, summon_position).append(picture.card_id)


    def delete(self, payload=None, card_id=None, quick_return=False):
        if payload is not None: card_id = payload['card_id']
        # delete from the group
        lookup = self.get_parameters()
        for val in lookup.keys():
            if card_id in getattr(self, val):
                getattr(self, val).remove(card_id)
        if quick_return: return
        # delete from lookup
        if card_id in self.picture_lookup:
            self.picture_lookup[card_id].delete()
            del self.picture_lookup[card_id]
            return True
        for opponent in self.opponents.keys():
            if self.opponents[opponent].delete(card_id=card_id): break

    def animate_cards(self, destination):
        positions = self.bounding_boxes[destination].card_positions(len(getattr(self, destination)))
        print(positions)
        for ind, i in enumerate(getattr(self, destination)):
            print("animate")
            print(i, (positions[ind], self.bounding_boxes[destination].center_y))
            animation = Animation(pos=(positions[ind], self.bounding_boxes[destination].center_y), t='out_back')
            if self.picture_lookup[i].scale != self.bounding_boxes[destination].scale:
                animation &= Animation(scale=self.bounding_boxes[destination].scale, t='in_out_cubic')
            animation.start(self.picture_lookup[i])

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
        self.opponents[opponent].load(payload)

    def remove_opponent(self,  name):
        if name in opponents: del opponents[name]
