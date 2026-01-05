Development notes

1. Create a virtual environment and install deps:

```
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Create `.env` from `.env.example` and edit values.

3. Run migrations (alembic must be installed in the env):

```
.\.venv\Scripts\python.exe -m alembic upgrade head
```

4. Start the server:

```
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

5. Run tests:

```
.\.venv\Scripts\pytest.exe -q
```
