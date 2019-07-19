/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
brew install wget
brew install tesseract --HEAD
brew install pkg-config sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer
pip3 install -r requirements.txt
wget -N https://archive.scryfall.com/json/scryfall-default-cards.json
wget -N https://github.com/oyyd/frozen_east_text_detection.pb/raw/master/frozen_east_text_detection.pb
brew install sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer
cd dependencies
git clone https://github.com/matham/kivy.git
cd kivy
git checkout async-support
python3 setup.py install
