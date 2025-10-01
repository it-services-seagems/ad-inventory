import requests
import json

URL = 'http://10.15.3.30:42057/api/warranty/bulk-refresh'
headers = {'Content-Type': 'application/json'}
payload = {'service_tags': ['SHQH2Z1ZP3']}

try:
    r = requests.post(URL, headers=headers, json=payload, timeout=15)
    print('STATUS', r.status_code)
    print('HEADERS')
    for k, v in r.headers.items():
        print(f'{k}: {v}')
    print('\nTEXT')
    print(r.text)
    try:
        j = r.json()
        print('\nJSON')
        print(json.dumps(j, indent=2, ensure_ascii=False))
    except Exception as e:
        print('No JSON:', e)
except Exception as e:
    print('REQUEST ERROR:', e)
