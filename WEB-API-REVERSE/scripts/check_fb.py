import asyncio
import json
import websockets

async def check():
    url = 'ws://127.0.0.1:54292/devtools/page/6B59AD37510877878CC927BF182858AE'
    async with websockets.connect(url) as ws:
        msg = {
            'id': 1,
            'method': 'Runtime.evaluate',
            'params': {'expression': 'document.title + " === " + (document.body ? document.body.innerText : "")'}
        }
        await ws.send(json.dumps(msg))
        res = await ws.recv()
        print('RESULT:', res)

if __name__ == '__main__':
    asyncio.run(check())
