import configparser, quinnat, asyncio, boto3, requests, os
from nio import Api, AsyncClient, RoomMessageText, RoomMessageImage

config = configparser.ConfigParser()
config.read('default.ini')

s3Url = config['S3']['s3Url']
s3AccessKey = config['S3']['s3AccessKey']
s3SecretKey = config['S3']['s3SecretKey']
s3Bucket = config['S3']['s3Bucket']

matrixRoom = config['MATRIX']['matrixRoom']
matrixBotUser = config['MATRIX']['matrixBotUser']
matrixBotPass = config['MATRIX']['matrixBotPass']
matrixHomeServer = config['MATRIX']['matrixHomeServer']

urbitUrl = config['URBIT']['urbitUrl']
urbitId = config['URBIT']['urbitId']
urbitCode = config['URBIT']['urbitCode']
urbitHost = config['URBIT']['urbitHost']
urbitBridgeChat = config['URBIT']['urbitBridgeChat']

if not os.path.exists('storage'):
    os.makedirs('storage')

s3Client = boto3.resource(
    service_name='s3',
    aws_access_key_id=s3AccessKey,
    aws_secret_access_key=s3SecretKey,
    endpoint_url=s3Url
)
s3BucketUrl = s3Url + '/' + s3Bucket

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

async def matrixTextListener(room, event):
    urbitClient.post_message(urbitHost, urbitBridgeChat, {"text": f"{room.user_name(event.sender)} in {room.display_name}: {event.body}"})

async def matrixImageListener(room, event):
    urbitClient.post_message(urbitHost, urbitBridgeChat, {"text": f"{room.user_name(event.sender)} in {room.display_name} posted an image:"})

    mxcSplit = event.url.split('/')
    imageDownloadRequest = requests.get(matrixHomeServer + Api.download(mxcSplit[2], mxcSplit[3])[1])
    with open('storage/' + event.body, 'wb') as f:
        f.write(imageDownloadRequest.content)
    s3Client.Bucket(s3Bucket).upload_file(
            Filename = 'storage/' + event.body,
            Key = event.body
    )
    s3AttachmentUrl = s3BucketUrl + '/' + event.body
    urbitClient.post_message(urbitHost, urbitBridgeChat, {"url": f"{s3AttachmentUrl}"})

async def main():
    urbitClient.connect()

    matrixClient = AsyncClient(matrixHomeServer, matrixBotUser)
    print(await matrixClient.login(matrixBotPass))
    matrixClient.add_event_callback(matrixTextListener, RoomMessageText)
    matrixClient.add_event_callback(matrixImageListener, RoomMessageImage)

    await matrixClient.sync_forever(timeout=30000)

asyncio.get_event_loop().run_until_complete(main())
