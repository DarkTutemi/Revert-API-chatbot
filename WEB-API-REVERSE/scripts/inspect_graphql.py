import urllib.request
import json

token = 're5q5W9DxzSJiJdVk1tE9hAgWDicvJFPyVOVPWBNJgi3gYX04fDTGVNCPMaZht3LRV'
url = 'http://127.0.0.1:9000/capture/live/filter'

payload = json.dumps({
    'filters': [
        {'type': 'keyword', 'pattern': 'graphql', 'caseSensitive': False}
    ]
}).encode()

req = urllib.request.Request(url, data=payload, method='POST')
req.add_header('Authorization', f'Bearer {token}')
req.add_header('Content-Type', 'application/json')

with urllib.request.urlopen(req) as resp:
    ids = json.loads(resp.read().decode())
    print(f'Total GraphQL records found: {len(ids)}')
    print('Recent IDs:', ids[-10:])
    
    for rid in ids[-5:]:
        get_req = urllib.request.Request(
            'http://127.0.0.1:9000/capture/live/get',
            data=json.dumps({'id': rid}).encode(),
            method='POST'
        )
        get_req.add_header('Authorization', f'Bearer {token}')
        get_req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(get_req) as gresp:
            detail = json.loads(gresp.read().decode())
            req_data = detail.get('request', {})
            res_data = detail.get('response', {}) or {}
            headers = {h['name'].lower(): h['value'] for h in req_data.get('headers', [])}
            body = req_data.get('body')
            friendly = headers.get('x-fb-friendly-name', 'N/A')
            status = res_data.get('code', 0)
            print('-------------------------------------------')
            print(f'ID: {rid} | [{req_data.get("method")}] {detail.get("url")} -> Status: {status}')
            print(f'Friendly Name: {friendly}')
            if body and isinstance(body, dict):
                text = body.get('text', '')
                if text:
                    print(f'Body Preview: {text[:200]}...')
