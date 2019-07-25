import socket
import asyncio

# request: action packet

class server:
    def __init__(self):
        self.rooms = {}
        self.users = {}
        self.current_id = 0
        self.server_actions = [
            "create_a_room", # name, password
            "join_a_room",
            "list_rooms",
            "my_room",
            "exit_room",
            "username",
            "help"
        ]

    def get_id(self):
        current_id = self.current_id
        self.current_id += 1
        return current_id

    def create_a_room(self, client_information, actions):
        if actions[1] in self.rooms:
            client_information.writer.write('could not create a room called {}, room already exists'.format(actions[1]).encode('utf-8'))
            return
        self.rooms[actions[1]] = {'password': actions[2], 'clients': {client_information.client_id: client_information.writer}}
        client_information.current_room = actions[1]
        client_information.writer.write('created a room called {}'.format(actions[1]).encode('utf-8'))
        if client_information.user_name is not None:
            client_information.client_to_client("Has joined the room.")
    
    def join_a_room(self, client_information, actions):
        if actions[1] in self.rooms and self.rooms[actions[1]]['password'] == actions[2]:
            client_information.writer.write('joined a room called {}'.format(actions[1]).encode('utf-8'))
            self.rooms[actions[1]]['clients'][client_information.client_id] = client_information.writer
            client_information.current_room = actions[1]
            if client_information.user_name is not None:
                client_information.client_to_client("Has joined the room.")
        else:
            client_information.writer.write('incorrect password for a room called {}'.format(actions[1]).encode('utf-8'))

    def list_rooms(self, client_information, actions):
        client_information.writer.write('{}'.format(self.rooms.keys()).encode('utf-8'))
    
    def my_room(self, client_information, actions):
        client_information.writer.write('{}'.format(client_information.current_room).encode('utf-8'))

    def exit_room(self, client_information, actions, write = True):
        if client_information.current_room is not None:
            if len(self.rooms[client_information.current_room]['clients']) == 1:
                del self.rooms[client_information.current_room]
            else:
                del self.rooms[client_information.current_room]['clients'][client_information.client_id]
            if client_information.user_name is not None:
                client_information.client_to_client("Has left the room.")
            client_information.current_room = None
            if write:
                client_information.writer.write('exited room'.encode('utf-8'))

    def username(self, client_information, actions):
        if actions[1] in self.users:
            client_information.writer.write('username already exists please select another'.encode('utf-8'))
            return
        if client_information.user_name is not None:
            del self.users[client_information.user_name]
        client_information.user_name = actions[1]
        self.users[client_information.user_name] = client_information.user_name
        client_information.writer.write('{} selected'.format(actions[1]).encode('utf-8'))
        if client_information.current_room is not None:
            client_information.client_to_client("Has joined the room.")
    
    def help(self, client_information, actions):
        client_information.writer.write('available commands: {}'.format(self.server_actions).encode('utf-8'))

class client_information:
    def __init__(self, reader, writer):
        global server_database
        self.server = server_database
        self.current_room = None
        self.user_name = None
        self.client_id = self.server.get_id()
        self.reader = reader
        self.writer = writer

    async def loop(self):
        request = None
        try:
            while True:
                    request = ""
                    while True:
                        packet = (await self.reader.read(1000)).decode('utf-8')
                        if packet == '': break
                        request += packet
                        if request.endswith('\n'): 
                            request = request[:-1]
                            break
                    if packet == '': break
                    actions = request.split(' ')
                    if actions[0] in self.server.server_actions:
                        getattr(self.server, actions[0])(self, actions)
                        continue
                    self.client_to_client(request)
        except Exception as e:
            pass
        self.exit()

    def client_to_client(self, request):
        if self.user_name is None:
            self.writer.write('please set a user name by username name'.encode('utf-8'))
            return
        if self.current_room is not None:
            request = (self.user_name + ": " + request).encode('utf-8')
            for client in self.server.rooms[self.current_room]['clients'].keys():
                if client == self.client_id:
                    continue
                self.server.rooms[self.current_room]['clients'][client].write(request)

    def exit(self):
        self.server.exit_room(self, actions = None, write = False)
        if self.user_name is not None:
            try:
                del self.server.users[self.user_name]
            except:
                pass
        self.writer.close()


async def handle_client(reader, writer):
    client = client_information(reader, writer)
    await client.loop()
    client.exit()

server_database = server()
loop = asyncio.get_event_loop()
loop.create_task(asyncio.start_server(handle_client, '0.0.0.0', 8080))
loop.run_forever()