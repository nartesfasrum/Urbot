import urlock
import dumper
import json

from botConfig import *

zod = urlock.Urlock(shipUrl, shipCode)
r = zod.connect()
s = zod.subscribe("zod", "chat-view", "/primary")

pipe = zod.sse_pipe()

# s = baseconvert.base(random.getrandbits(128), 10, 32, string=True).lower()
# uid = '0v' + '.'.join(s[i:i+5] for i in range(0, len(s), 5))[::-1]

# p = zod.poke("zod", "chat-hook", "json", {"message": {"path": "/~/~zod/mc",
#                                                       "envelope": {"uid": uid,
#                                                                    "number": 1,
#                                                                    "author": "~zod",
#                                                                    "when": int(time.time() * 1000),
#                                                                    "letter": {"text": "hello world!"}}}})

for m in pipe.events():
   zod.ack(int(m.id))
   parsedMessage = m.data.split("'")
   dumper.dump(parsedMessage)
   print()
