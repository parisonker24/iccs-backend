

import urllib.request, json, sys
base='http://127.0.0.1:8000'
# Create product
prod={'name':'test-product','description':'desc','price':9.99}
req=urllib.request.Request(base+'/products/', data=json.dumps(prod).encode(), headers={'Content-Type':'application/json'})
try:
    resp=urllib.request.urlopen(req)
    body=resp.read().decode()
    print('POST /products/', resp.getcode(), body)
    prod_resp=json.loads(body)
    pid=prod_resp.get('id')
except Exception as e:
    print('product create error', e)
    sys.exit(1)
# Create inventory
inv={'product_id': pid, 'quantity': 5, 'location': 'warehouse'}
req2=urllib.request.Request(base+'/inventory/', data=json.dumps(inv).encode(), headers={'Content-Type':'application/json'})
try:
    resp2=urllib.request.urlopen(req2)
    body2=resp2.read().decode()
    print('POST /inventory/', resp2.getcode(), body2)
except Exception as e:
    import traceback
    print('inventory create error', e)
    traceback.print_exc()
    sys.exit(1)
    print('Created product id=', pid)
