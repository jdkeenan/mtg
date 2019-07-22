# Magic the Gathering
This was a project created during Formlabs hackathon as a way for us to play magic easier with remote offices. Please note that magic is not affeliated with us in anyway and we encourage you to support the game through the purchase of cards or through their official client "magic the gathering arena". This game is designed to supplement players that already own physical cards and want to play with friends using their physical cards remotely.

# Client/Server Connections
This game uses scryfall card database to lookup either scanned or typed in cards that you have in and creates them in the online client. Currently we have a server running that will accept client connections, the interfaces and systems are pretty sloppy due to the time crunch. If you want to play I would reccomend setting up your own server, change the linked url from the client and run the server.py script on the server or looking at the accepted client communications to use the setup server.

# Install
In order to download the game we've built a "quick" install.sh bash script running that "should" download all of the needed dependicies. If we have a demand/when the game is more polished, I'll probably make a mac application to make it easier to download and get playing.

# Speed up by downloading the cards before playing
If you are waiting awhile on cards to download it might be worthwhile to run the card_search.py script. It's not needed to play the game as cards will be downloaded as you type or scan them in, but it will make scanning/playing much faster.

# Run the game
To run the game just type in python3 ui.py.
