from jose import jwt
import time
import requests
from app.core.config import settings

def make_token():
    payload = {"sub": "1", "role": "admin", "exp": int(time.time()) + 3600}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

if __name__ == '__main__':
    token = make_token()
    url = 'http://127.0.0.1:8000/reports/weekly-sales?tz=UTC&include_totals=true'
    headers = {'Authorization': f'Bearer {token}'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print('STATUS', r.status_code)
        print(r.text)
    except Exception as e:
        print('ERROR', e)
