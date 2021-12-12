import asyncio, os, quinnat
from base_bridge import *
from helpers import get_json_dump
from multiprocessing import active_children, Process
from nio import AsyncClient, ClientConfig, MatrixRoom, RoomMessageText

class matrix_client(generic_bridge):
    def __init__(self, instance, urb_info):
        super().__init__(instance)
        print("initialising matrix_client...")
        self.urb_info = urb_info
        self.instance = instance
        self.bot_user = instance["matrix_bot_user"]
        self.bot_password = instance["matrix_bot_pass"]
        self.device_id = instance["matrix_device_id"]
        self.homeserver = instance["matrix_homeserver"]
        self.store_path = instance["matrix_store_path"]
        self.channel_list = []
        self.config = ClientConfig(store_sync_tokens=True, encryption_enabled=True)
        self.matrixClient = AsyncClient(self.homeserver, self.bot_user, device_id=self.device_id, store_path=self.store_path, config=self.config)

        for channel_group in instance["channels"]:
            self.channel_list.append(channel_group["matrix_room"])

    async def send(self, room, body):
        await self.matrixClient.room_send(
            room_id = room,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": body
            }
        )
        print("message sent!")

class urbit_client:
    def __init__(self, instance):
        self.instance = instance
        self.connect()

    def connect(self):
        self.client = quinnat.Quinnat(
                self.instance["urbit_url"],
                self.instance["client_ship"],
                self.instance["urbit_code"]
        )
        print("connecting urbit_client...")
        self.client.connect()

    def send(self, resource_ship, channel, message):
        try:
            self.client.post_message(
                    resource_ship,
                    channel,
                    {"text": message}
            )
        except UnicodeDecodeError:
            self.reconnect()

    def reconnect(self):
        self.client.ship.delete()
        self.client = self.connect()

class bridge():
    def __init__(self, instance, urb_info, matrix_client):
        self.instance = instance
        self.urbit_client = urbit_client(urb_info)
        self.urb_info = urb_info
        self.matrix_client = matrix_client

    def start(self):
        for channel in self.instance["channels"]:
            self.urbit_client.send(channel['resource_ship'], channel['urbit_channel'], "Urbot has connected to this channel!")
        async def urbit_message_handler(message, _):
            matched_ships = list(filter(lambda ship: ship["resource_ship"] == message.host_ship, self.instance["channels"]))
            if len(matched_ships) > 0:
                for matched_ship in matched_ships:
                    if matched_ship["urbit_channel"] == message.resource_name:
                        message_body = message.author + ": " + message.full_text
                        print("attempting to send message to Matrix...")
                        print("message to be sent: ", message_body)
                        print("message to room: ", matched_ship["matrix_room"])

        def urbit_listener(message, _):
            asyncio.run(urbit_message_handler(message, _))

        while True:
            try:
                print("starting urbit listener...")
                self.urbit_client.client.listen(urbit_listener)
            except UnicodeDecodeError:
                self.urbit_client.reconnect()
                continue


    async def matrix_message_handler(self, room: MatrixRoom, event: RoomMessageText):
        matched_channels = list(filter(lambda channel: channel["matrix_room"] == room.machine_name, self.instance["channels"]))
        for matched_channel in matched_channels:
            message_body = room.user_name(event.sender) + ": " + event.body
            print("attempting to send message to Urbit...")
            print("message to be sent: ", message_body)
            print("message to channel:", matched_channel["urbit_channel"])
            self.urbit_client.send(matched_channel["resource_ship"], matched_channel["urbit_channel"], message_body)

async def main():
    procs = []

    for instance in get_json_dump("config.json"):
        print("dumping json...")
        urb_info = {
                "urbit_url": instance["urbit_url"],
                "client_ship": instance["client_ship"],
                "urbit_code": instance["urbit_code"]
                }

        for bot in instance["bots"]:
            if bot["type"] == "matrix":
                print("setting up bots...")
                matrix_instance = matrix_client(bot, urb_info)
                bridge_instance = bridge(bot, urb_info, matrix_instance)
            else:
                raise Exception("bot type not implemented!")

            print("starting processes...")
            response = await matrix_instance.matrixClient.login(matrix_instance.bot_password)
            print(response)
            bridge_proc = Process(target=bridge_instance.start)

            bridge_proc.start()
            procs.append(bridge_proc)
    
    matrix_instance.matrixClient.add_event_callback(bridge_instance.matrix_message_handler, RoomMessageText)

    await matrix_instance.matrixClient.sync_forever(timeout=30000, full_state=True)

asyncio.get_event_loop().run_until_complete(main())
