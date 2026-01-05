import httpx
from typing import Any, Dict


class _Response:
    def __init__(self, resp: httpx.Response):
        self._resp = resp
        self.status_code = resp.status_code

    def json(self) -> Any:
        return self._resp.json()


def post(url: str, json: Dict = None, **kwargs) -> _Response:
    resp = httpx.post(url, json=json, **kwargs)
    return _Response(resp)


def get(url: str, params: Dict = None, **kwargs) -> _Response:
    resp = httpx.get(url, params=params, **kwargs)
    return _Response(resp)
