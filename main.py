import configparser, quinnat, asyncio
from nio import AsyncClient, RoomMessageText

config = configparser.ConfigParser()
config.read('default.ini')

matrixRoom = config['MATRIX']['matrixRoom']
matrixBotUser = config['MATRIX']['matrixBotUser']
matrixBotPass = config['MATRIX']['matrixBotPass']
matrixHomeServer = config['MATRIX']['matrixHomeServer']

urbitUrl = config['URBIT']['urbitUrl']
urbitId = config['URBIT']['urbitId']
urbitCode = config['URBIT']['urbitCode']
urbitHost = config['URBIT']['urbitHost']
urbitBridgeChat = config['URBIT']['urbitBridgeChat']

urbitClient = quinnat.Quinnat(urbitUrl, urbitId, urbitCode)

async def urbitListener(message, replier):
    await matrixClient.room_send(
            room_id=matrixRoom,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": message.full_text
            }
    )

async def matrixListener(room, event):
    urbitClient.post_message(urbitHost, urbitBridgeChat, {"text": f"Got message from {room.user_name(event.sender)} in {room.display_name}: {event.body}"})

async def main():
    urbitClient.connect()

    matrixClient = AsyncClient(matrixHomeServer, matrixBotUser)
    print(await matrixClient.login(matrixBotPass))
    matrixClient.add_event_callback(matrixListener, RoomMessageText)

    await matrixClient.sync_forever(timeout=30000)

asyncio.get_event_loop().run_until_complete(main())
