import json
import sys
import urllib.request

BASE = 'http://127.0.0.1:8000'

product_payload = {
    "name": "Sample product",
    "description": "Created by assistant",
    "price": 9.99,
    "vendor_id": None
}

def post(path, payload):
    url = BASE + path
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode('utf-8')

try:
    prod_resp = post('/products/', product_payload)
    print('PRODUCT_RESPONSE:')
    print(prod_resp)
    prod = json.loads(prod_resp)
    prod_id = prod.get('id') or prod.get('ID') or prod.get('pk')
    if not prod_id:
        print('Could not determine product id from response', file=sys.stderr)
        sys.exit(2)

    inventory_payload = {"product_id": prod_id, "quantity": 10, "location": "Warehouse A"}
    inv_resp = post('/inventory/', inventory_payload)
    print('\nINVENTORY_RESPONSE:')
    print(inv_resp)
except Exception as e:
    print('ERROR:', e, file=sys.stderr)
    raise
