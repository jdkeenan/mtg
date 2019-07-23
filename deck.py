import random
import json


class Deck:
    def __init__(self, json_deck = 'fire_deck.json'):
        with open(json_deck, 'r') as f:
            data = json.load(f)
        self.deck = data['deck']
        self.index = 6

    def load_hand(self):
        random.shuffle(self.deck)
        return self.deck[:7]

    def load_card(self):
        self.index += 1
        if self.index == 61: return None
        return self.deck[self.index]

if __name__ == '__main__':
    deck = Deck()
    for i in  deck.load_hand():
        print(i)
    current_card = deck.load_card()
    while current_card is not None:
        input("Press Enter to continue...")
        print(current_card)
        current_card = deck.load_card()
