import urllib.request
import json
import sys

# Set stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

token = 're5q5W9DxzSJiJdVk1tE9hAgWDicvJFPyVOVPWBNJgi3gYX04fDTGVNCPMaZht3LRV'
url = 'http://127.0.0.1:9000/capture/live/filter'

payload = json.dumps({
    'filters': [
        {'type': 'keyword', 'pattern': '/api/graphql/', 'caseSensitive': False}
    ]
}).encode()

req = urllib.request.Request(url, data=payload, method='POST')
req.add_header('Authorization', f'Bearer {token}')
req.add_header('Content-Type', 'application/json')

with urllib.request.urlopen(req) as resp:
    ids = json.loads(resp.read().decode())
    print(f'Total /api/graphql/ records found: {len(ids)}')
    print('Record IDs:', ids)
    
    for rid in ids:
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
            target_url = detail.get('url', '')
            if 'facebook.com/api/graphql' in target_url:
                print('-------------------------------------------')
                print(f'ID: {rid} | [{req_data.get("method")}] {target_url} -> Status: {status}')
                print(f'Action (x-fb-friendly-name): {friendly}')
                # Parse form data body if available
                if body and isinstance(body, dict):
                    raw_text = body.get('text', '')
                    if raw_text:
                        # Extract fb_api_caller_class or other params
                        print(f'Body Snippet: {raw_text[:150]}...')
