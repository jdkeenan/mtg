import json
import urllib
import cv2
import os
import requests
import re
import difflib


class card_database_creation:
    SCRY_JSON_CARD_DATABASE = 'scryfall-default-cards.json'
    def __init__(self):
        self.regex = re.compile('[^a-z]')
        with open(self.SCRY_JSON_CARD_DATABASE, 'r') as f:
            temp_card_lookup = json.load(f)
        self.card_lookup = {}
        for card in temp_card_lookup:
            name = self.regex.sub('', card['name'].lower())
            while name in self.card_lookup:
                name += '|'
            self.card_lookup[name] = card
        if not os.path.isdir('cards'):
            os.mkdir('cards')


class card_creation:
    def __init__(self, card_database, name):
        self.card_database = card_database
        name = self.card_database.regex.sub('', name.lower())
        if name not in self.card_database.card_lookup:
            name = difflib.get_close_matches(name, self.card_database.card_lookup.keys())[0]
        self.path = os.path.join('cards', name)
        self.name = name
        self.information = self.card_database.card_lookup[name]
        self.card_images = {}
        if not os.path.isdir(self.path): # download the pngs
            os.mkdir(self.path)
            self.download_card(name)

    def download_card(self, name):
        for image in self.information['image_uris'].keys():
            url = self.information['image_uris'][image]
            r = requests.get(url, allow_redirects=True)
            if r.status_code != 200:
                if name + '|' not in self.card_database.card_lookup:
                    print("failed to load card")
                    return
                self.information = self.card_database.card_lookup[name + '|']
                return self.download_card(name + '|')
            open(os.path.join(self.path, image) + self.ending(image), 'wb').write(r.content)

    def __getattr__(self, name):
        if name not in self.card_images: 
            self.card_images[name] = os.path.join(self.path, name + self.ending(name))
        return self.card_images[name]

    @staticmethod
    def ending(name):
        if name == 'png': ending = '.png'
        else: ending = '.jpg'
        return ending

    def show(self, name):
        cv2.imshow('img', getattr(self, name))
        cv2.waitKey(0)

if __name__ == '__main__':
    name = 'Nicol Bolas, Dragon-God'
    card_database = card_database_creation()
    card = card_creation(card_database, 'sire of stagnation')
    print('done')
    # card = card_creation(card_database, 'OjotaiSoalofWlnter')

    # card = card_creation(card_database, name)
    cv2.imshow('img', cv2.imread(card.png))
    cv2.waitKey(0)
