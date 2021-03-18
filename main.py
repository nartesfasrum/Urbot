import configparser, quinnat, asyncio
from nio import AsyncClient

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

async def main():
    urbitClient = quinnat.Quinnat(urbitUrl, urbitId, urbitCode)
    urbitClient.connect()
    matrixClient = AsyncClient(matrixHomeServer, matrixBotUser)
    print(await matrixClient.login(matrixBotPass))
    await matrixClient.room_send(
            room_id=matrixRoom,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": "ping"
            }
    )
    await matrixClient.close()

asyncio.get_event_loop().run_until_complete(main())
