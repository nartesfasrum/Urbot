import asyncio, json, os, sys, quinnat
from helpers import get_json_dump
from multiprocessing import active_children, Process
from nio import AsyncClient, ClientConfig, InviteEvent, LoginResponse, LocalProtocolError, MatrixRoom, MatrixUser, RoomMessageText, crypto, exceptions, RoomSendResponse

class MatrixClient(AsyncClient):
    def __init__(self, homeserver, user='', device_id='', store_path='', config=None, ssl=None, proxy=None, password='', session_details_file='matrix_credentials_cache.json'):
        super().__init__(homeserver, user=user, device_id=device_id, store_path=store_path, config=config, ssl=ssl, proxy=proxy)
        if store_path and not os.path.isdir(store_path):
            os.mkdir(store_path)

        self.session_details_file = session_details_file
        self.password = password

    async def login(self):
        if os.path.exists(self.session_details_file) and os.path.isfile(self.session_details_file):
            try:
                with open("matrix_credentials_cache.json", "r") as f:
                    config = json.load(f)
                    self.access_token = config['access_token']
                    self.user_id = config['user_id']
                    self.device_id = config['device_id']

                    self.load_store()
                    print(f"Logged in using stored credentials: {self.user_id} on {self.device_id}")

            except IOError as err:
                print(f"Couldn't load session from file. Logging in. Error: {err}")
            except json.JSONDecodeError:
                print("Couldn't read JSON file! Overwriting...")

        if not self.user_id or not self.access_token or not self.device_id:
            response = await super().login(self.password)

            if isinstance(response, LoginResponse):
                print("Logged in using a password. Saving credentials to disk...")
                self.__write_details_to_disk(response)
            else:
                print(f"Failed to log in! Response: {resp}")
                sys.exit(1)

    async def message_send(self, room, body):
        try:
            await self.room_send(
                room_id = room,
                message_type="m.room.message",
                content={
                    "msgtype": "m.text",
                    "body": body
                }
            )
            print("message sent!")
        except exceptions.OlmUnverifiedDeviceError as err:
            print("Known devices: ")
            device_store: crypto.DeviceStore = device_store
            [print(f"\t{device.user_id}\t {device.device_id}\t {device.trust_state}\t  {device.display_name}") for device in device_store]
            sys.exit(1)

    def cb_autojoin_room(self, room: MatrixRoom, event: InviteEvent):
        print(f"Joining invited room {room.name}...")
        self.join(room.room_id)
        room = self.rooms[ROOM_ID]
        print(f"Is {room.name} encrypted: {room.encrypted}")

    async def cb_message_text(self, room: MatrixRoom, event: RoomMessageText):
        if event.decrypted:
            encrypted_symbol = "e "
        else:
            encrypted_symbol = "u "
        print(f"{room.display_name} | {encrypted_symbol}| {room.user_name(event.sender)}: {event.body}")

    @staticmethod
    def __write_details_to_disk(resp: LoginResponse):

        with open("matrix_credentials_cache.json", "w") as f:
            json.dump({
                "access_token": resp.access_token,
                "device_id": resp.device_id,
                "user_id": resp.user_id
            }, f)

async def run_matrix_client(client: MatrixClient):
    await client.login()

    async def after_first_sync():
        print("Awaiting sync...")
        await client.synced.wait()

    after_first_sync_task = asyncio.create_task(after_first_sync())

    sync_forever_task = asyncio.ensure_future(client.sync_forever(30000, full_state=True))

    await asyncio.gather(
        after_first_sync_task,
        sync_forever_task
    )

async def main():
    for instance in get_json_dump("config.json"):
        for bot in instance["bots"]:
            config = ClientConfig(store_sync_tokens=True)
            matrix_client = MatrixClient(bot["matrix_homeserver"], bot["matrix_bot_user"], store_path=bot["matrix_store_path"], config=config, password=bot["matrix_bot_pass"])
            matrix_client.add_event_callback(matrix_client.cb_autojoin_room, InviteEvent)
            matrix_client.add_event_callback(matrix_client.cb_message_text, RoomMessageText)

            try:
                await run_matrix_client(matrix_client)
            except (asyncio.CancelledError, KeyboardInterrupt):
                await matrix_client.close()

if __name__ == "__main__":
    try:
        asyncio.run(
            main()
        )
    except KeyboardInterrupt:
        pass
