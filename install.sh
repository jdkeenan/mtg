pip3 install -r requirements.txt
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
brew install wget
wget https://archive.scryfall.com/json/scryfall-default-cards.json
brew install sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer
cd dependencies
git clone https://github.com/matham/kivy.git
cd kivy
git checkout async-support
python3 setup.py install
