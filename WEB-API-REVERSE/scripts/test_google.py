import asyncio
import json
import websockets

async def check():
    url = 'ws://127.0.0.1:1295/devtools/page/6328F892274EB928C60C7A8939877982'
    async with websockets.connect(url) as ws:
        # Navigate to google
        msg = {
            'id': 1,
            'method': 'Page.navigate',
            'params': {'url': 'https://www.google.com'}
        }
        await ws.send(json.dumps(msg))
        await ws.recv()
        await asyncio.sleep(3)

        msg2 = {
            'id': 2,
            'method': 'Runtime.evaluate',
            'params': {'expression': 'document.title + " === " + (document.body ? document.body.innerText.substring(0, 300) : "")'}
        }
        await ws.send(json.dumps(msg2))
        res = await ws.recv()
        print('GOOGLE RESULT:', res)

if __name__ == '__main__':
    asyncio.run(check())
