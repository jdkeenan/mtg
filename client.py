import asyncio
# from aioconsole import ainput

# async def tcp_echo_client(message):
#     reader, writer = await asyncio.open_connection('3.90.36.188', 8080)
#     async def reader_tcp():
#         while True:
#             data = await reader.read(4096)
#             print(data)
#     async def writer_tcp():
#         while True:
#             message = await ainput(">>>")
#             writer.write(message.encode())
#     await asyncio.gather(*[reader_tcp(), writer_tcp()])
#     writer.close()

# loop = asyncio.get_event_loop()
# loop.run_until_complete(tcp_echo_client('Hello'))

class client_connection:
    IP = '3.90.36.188'

    async def establish_connection(self):
        self.reader, self.writer = await asyncio.open_connection(self.IP, 8080)

    def writer_tcp(self, message):
        self.writer.write(message.encode())

    async def reader_tcp(self, call_back):
        while True:
            data = await self.reader.read(4096)
            call_back(data.decode())

    def close(self):
        self.writer.close()

if __name__ == '__main__':
    from aioconsole import ainput

    async def tcp_echo_client(message):
        reader, writer = await asyncio.open_connection('3.90.36.188', 8080)
        async def reader_tcp():
            while True:
                data = await reader.read(4096)
                print(data)
        async def writer_tcp():
            while True:
                message = await ainput(">>>")
                writer.write(message.encode())
        await asyncio.gather(*[reader_tcp(), writer_tcp()])
        writer.close()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(tcp_echo_client('Hello'))
