import json
import urllib
import cv2
import os
import requests
import re
import difflib
import glob
import logging
import threading
import time
import numpy as np

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
            matches = difflib.get_close_matches(name, self.card_database.card_lookup.keys())
            if len(matches) == 0: return
            name = matches[0]
        self.path = os.path.join('cards', name)
        self.name = name
        self.information = self.card_database.card_lookup[name]
        self.card_images = {}
        if not os.path.isdir(self.path): # download the pngs
            os.mkdir(self.path)
            self.download_card(name)

    def download_card(self, name):
        if 'image_uris' not in self.information: return
        for image in self.information['image_uris'].keys():
            if image not in ['normal', 'art_crop']: continue
            url = self.information['image_uris'][image]
            r = requests.get(url, allow_redirects=True)
            if r.status_code != 200:
                if name + '|' not in self.card_database.card_lookup:
                    print("failed to load card")
                    os.rmdir(self.path)
                    return False
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

def all_the_cards(diff):
    for card_name in diff:
        if len(card_name) == 0: continue
        if card_name[-1] == '|': continue
        card = card_creation(card_database, card_name)

if __name__ == '__main__':
    threads = 10
    card_list = []
    thread_chunk = []
    jobs = []
    card_database = card_database_creation()
    diff = set(card_database.card_lookup) - set(glob.glob(os.path.join('cards', '*')))
    for card_name in diff:
        if len(card_name) == 0: continue
        if card_name[-1] == '|': continue
        card_list.append(card_name)
    increment = int(len(card_list) / threads)
    card_list = sorted(card_list)
    for i in range(0, len(card_list), increment):
        thread_chunk.append(card_list[i:i+increment])
    print(thread_chunk)
    for i in range(0, threads):
        print(thread_chunk[i])
    for i in range(0, len(thread_chunk)):
        print(thread_chunk[i])
        out_list = list()
        thread = threading.Thread(target=all_the_cards, kwargs={'diff': thread_chunk[i]})
        jobs.append(thread)
    for j in jobs:
        j.start()
    for j in jobs:
        j.join()

#    card_database = card_database_creation()
#    diff = set(card_database.card_lookup) - set(glob.glob(os.path.join('cards', '*')))
#    for card_name in diff:
#        if len(card_name) == 0: continue
#        if card_name[-1] == '|': continue
#        card = card_creation(card_database, card_name)
#        jobs.append(thread)
#        print(card_name)
    
    #card = card_creation(card_database, 'OjotaiSoalofWlnter')
    #cv2.imshow('img', cv2.imread(card.png))
    #cv2.waitKey(0)
