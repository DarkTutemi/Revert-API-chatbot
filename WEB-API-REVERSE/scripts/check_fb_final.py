import asyncio
import json
import websockets

async def check():
    url = 'ws://127.0.0.1:52029/devtools/page/23C9B9BF724CC4E27E3FAC3371672949'
    async with websockets.connect(url) as ws:
        msg = {
            'id': 1,
            'method': 'Runtime.evaluate',
            'params': {'expression': 'document.title + " === " + (document.body ? document.body.innerText.substring(0, 300) : "")'}
        }
        await ws.send(json.dumps(msg))
        res = await ws.recv()
        print('FACEBOOK RESULT:', res)

if __name__ == '__main__':
    asyncio.run(check())
