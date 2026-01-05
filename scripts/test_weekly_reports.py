from fastapi.testclient import TestClient
from app.main import app
from jose import jwt
from app.core.config import settings
import datetime

payload = {"sub": "1", "role": "admin", "exp": int((datetime.datetime.utcnow()+datetime.timedelta(hours=1)).timestamp())}
token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
client = TestClient(app)
resp = client.get('/reports/weekly-sales?tz=UTC&include_totals=true', headers={'Authorization': f'Bearer {token}'})
print('STATUS', resp.status_code)
try:
    print(resp.json())
except Exception as e:
    print('RAW:', resp.text)
