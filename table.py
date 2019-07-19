import ast
from card_search import card_database_creation, card_creation
from picture import Picture

class Table:
    def __init__(self, parent, opponent=False):
        self.parent = parent
        self.opponent = opponent
        self.monsters = []
        self.attacking_cards = []
        self.mana_cards = []
        self.hand = []
        self.opponents = {}
        self.picture_lookup = {}

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

    def _getmonsters(self):
        return self.establish_cards(self.monsters)

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
            # print(summon_position)
            # print(getattr(self, summon_position))
            getattr(self, summon_position).append(picture.card_id)
            # print(getattr(self, summon_position))


    def delete(self, payload=None, card_id=None):
        if payload is not None: card_id = payload['card_id']
        # delete from the group
        lookup = self.get_parameters()
        for val in lookup.keys():
            if card_id in getattr(self, val):
                getattr(self, val).remove(card_id)
        # delete from lookup
        if card_id in self.picture_lookup:
            self.picture_lookup[card_id].delete()
            del self.picture_lookup[card_id]
            return True
        for opponent in self.opponents.keys():
            if self.opponents[opponent].delete(card_id=card_id): break

    # opponent updates
    def opponent_update(self, opponent, payload):
        if opponent not in self.opponents:
            self.opponents[opponent] = Table(self.parent, opponent=True)
        self.opponents[opponent].load(payload)

    def remove_opponent(self,  name):
        if name in opponents: del opponents[name]
