import asyncio, boto3, json, os, requests, sys, quinnat
from helpers import get_json_dump
from multiprocessing import active_children, Process
from nio import Api, AsyncClient, ClientConfig, InviteEvent, LoginResponse, LocalProtocolError, MatrixRoom, MatrixUser, RoomEncryptedMedia, RoomMessageMedia, RoomMessageText, RoomSendResponse, crypto, exceptions

class bridge:
    def __init__(self, matrix_client, s3_client, urbit_client, instance):
        self.matrix_client = matrix_client
        self.urbit_client = urbit_client
        self.s3_client = s3_client
        self.instance = instance

        self.add_callbacks()

        for channel in self.instance["channels"]:
            self.urbit_client.message_send(channel['resource_ship'], channel['urbit_channel'], "Urbot has connected to this channel!")

    def cb_autojoin_room(self, room: MatrixRoom, event: InviteEvent):
        print(f"Joining invited room {room.name}...")
        self.matrix_client.join(room.room_id)
        room = self.matrix_client.rooms[ROOM_ID]
        print(f"Is {room.name} encrypted: {room.encrypted}")

    def cb_message_media(self, room, event):
        matched_channels = self.match_channels(room)
        for matched_channel in matched_channels:
            message_body = room.user_name(event.sender) + " sent an encrypted file: "
            self.urbit_client.message_send(matched_channel["resource_ship"], matched_channel["urbit_channel"], message_body)

            mxc_split = event.url.split('/')
            image_download_request = requests.get(self.matrix_client.homeserver + Api.download(mxc_split[2], mxc_split[3])[1])
            s3_attachment_url = self.s3_client.upload(event.body, image_download_request.content)
            self.urbit_client.log_urbit_message(s3_attachment_url, matched_channel["urbit_channel"])
            self.urbit_client.client.post_message(matched_channel["resource_ship"], matched_channel["urbit_channel"], {"url": f"{s3_attachment_url}"})

    def cb_message_text(self, room: MatrixRoom, event: RoomMessageText):
        matched_channels = self.match_channels(room)
        for matched_channel in matched_channels:
            message_body = room.user_name(event.sender) + ": " + event.body
            self.urbit_client.message_send(matched_channel["resource_ship"], matched_channel["urbit_channel"], message_body)

    def add_callbacks(self):
        self.matrix_client.add_event_callback(self.cb_autojoin_room, InviteEvent)
        self.matrix_client.add_event_callback(self.cb_message_media, RoomEncryptedMedia)
        self.matrix_client.add_event_callback(self.cb_message_media, RoomMessageMedia)
        self.matrix_client.add_event_callback(self.cb_message_text, RoomMessageText)


    def match_channels(self, room):
        matched_channels = list(filter(lambda channel: channel["matrix_room"] == room.machine_name, self.instance["channels"]))
        return matched_channels

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


    @staticmethod
    def __write_details_to_disk(resp: LoginResponse):

        with open("matrix_credentials_cache.json", "w") as f:
            json.dump({
                "access_token": resp.access_token,
                "device_id": resp.device_id,
                "user_id": resp.user_id
            }, f)

class S3Client:
    def __init__(self, instance):
        self.instance = instance

        self.s3_client = boto3.resource(
            service_name = 's3',
            aws_access_key_id = self.instance["s3_key_access"],
            aws_secret_access_key = self.instance["s3_key_secret"],
            endpoint_url = self.instance["s3_url"]
        )

    def upload(self, event_body, image_download_request_content):
        with open(self.instance["matrix_store_path"] + event_body, 'wb') as f:
            f.write(image_download_request_content)
        self.s3_client.Bucket(self.instance["s3_bucket"]).upload_file(
            Filename = self.instance["matrix_store_path"] + event_body,
            Key = event_body
        )

        s3_attachment_url = self.instance["s3_url"] + '/' + self.instance["s3_bucket"] + '/' + event_body

        return s3_attachment_url

class UrbitClient:
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

    def log_urbit_message(self, message, channel):
        print("Attempting to forward event to Urbit...")
        print("Event to be sent: ", message)
        print("Event to channel: ", channel)

    def message_send(self, resource_ship, channel, message):
        try:
            self.log_urbit_message(message, channel)
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
        urbit_config = {
            "urbit_url": instance["urbit_url"],
            "client_ship": instance["client_ship"],
            "urbit_code": instance["urbit_code"]
        }

        for bot in instance["bots"]:
            matrix_config = ClientConfig(store_sync_tokens=True)

            matrix_client = MatrixClient(bot["matrix_homeserver"], bot["matrix_bot_user"], store_path=bot["matrix_store_path"], config=matrix_config, password=bot["matrix_bot_pass"])
            s3_client = S3Client(bot)
            urbit_client = UrbitClient(urbit_config)
            bridge_instance = bridge(matrix_client, s3_client, urbit_client, bot)

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
