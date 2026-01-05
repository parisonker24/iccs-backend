import json
import urllib.request
import sys

url = "http://127.0.0.1:8001/users/"
payload = {
	"username": "Abraham",
	"email": "abrahim@gmail.com",
	"password": "abrahim2424",
}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data, headers={"Content-Type": "application/json"})
try:
	with urllib.request.urlopen(req) as resp:
		print(resp.status)
		print(resp.read().decode())
except Exception:
	import traceback

	traceback.print_exc()
	sys.exit(1)
