"""HTTP client for a local Laya System One server."""

from urllib.parse import urlsplit

import aiohttp


class LayaConnectionError(Exception):
    """The configured Laya server is unreachable or incompatible."""


def normalize_url(value: str) -> str:
    """Accept only a server origin, never a URL with embedded credentials."""
    value = value.strip().rstrip("/")
    parsed = urlsplit(value)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username
            or parsed.password or parsed.path or parsed.query or parsed.fragment):
        raise ValueError("Enter only an http(s) Laya server origin, such as http://host:8000")
    return value


class LayaClient:
    def __init__(self, session: aiohttp.ClientSession, url: str, api_key: str = "") -> None:
        self.session = session
        self.url = normalize_url(url)
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    async def check(self) -> None:
        try:
            async with self.session.get(
                self.url + "/health", headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=10), allow_redirects=False,
            ) as response:
                body = await response.json()
                if response.status != 200 or not isinstance(body, dict) or body.get("status") != "ok":
                    raise LayaConnectionError("Laya health endpoint did not return status ok")
        except (aiohttp.ClientError, TimeoutError, ValueError) as exc:
            raise LayaConnectionError("Cannot reach a compatible Laya server") from exc
        answers = await self.ask({
            "model": "multilingual",
            "state": {"request": "connection test"},
            "questions": {"probe": {"type": "choice", "instructions": "Is this a connection test?",
                                    "criteria": {"yes": "a test", "no": "something else"}}},
        })
        if not isinstance(answers.get("probe"), dict):
            raise LayaConnectionError("Laya server did not return a choice answer")

    async def ask(self, request: dict) -> dict:
        try:
            async with self.session.post(
                self.url + "/v1/systemone", json=request, headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=30), allow_redirects=False,
            ) as response:
                if response.status != 200:
                    raise LayaConnectionError(f"Laya returned HTTP {response.status}")
                result = await response.json()
            if not isinstance(result, dict) or not isinstance(result.get("answers"), dict):
                raise LayaConnectionError("Laya returned an invalid answer")
            return result["answers"]
        except (aiohttp.ClientError, TimeoutError, ValueError) as exc:
            raise LayaConnectionError("Laya request failed") from exc
