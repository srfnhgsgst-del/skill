from typing import Optional
import httpx


class BaseHttpClient:
    """HTTP 基础客户端 — 封装会话管理/超时/重试/cookie/错误处理"""

    DEFAULT_HEADERS: dict[str, str] = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    BASE_URL: str = ""
    MAX_RETRIES = 2
    RETRY_STATUSES = {429, 500, 502, 503, 504}

    def __init__(self, timeout: float = 30.0, cookies: Optional[dict] = None):
        self.timeout = timeout
        self._cookies: dict[str, str] = dict(cookies or {})
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            headers = dict(self.DEFAULT_HEADERS)
            if self.BASE_URL:
                headers.setdefault("Referer", self.BASE_URL + "/")
            self._client = httpx.Client(
                headers=headers,
                cookies=dict(self._cookies),
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    def close(self):
        if self._client:
            self._client.close()
            self._client = None

    def _update_cookies(self, response: httpx.Response):
        for cookie in response.cookies:
            self._cookies[cookie.name] = cookie.value

    def request(
        self, method: str, url: str, **kwargs
    ) -> httpx.Response:
        last_exc = None
        for attempt in range(1 + self.MAX_RETRIES):
            try:
                resp = self.client.request(method, url, **kwargs)
                self._update_cookies(resp)
                if resp.status_code in self.RETRY_STATUSES and attempt < self.MAX_RETRIES:
                    import time
                    time.sleep(1.0 * (attempt + 1))
                    continue
                resp.raise_for_status()
                return resp
            except (httpx.TimeoutException, httpx.HTTPStatusError,
                    httpx.ConnectError, httpx.RemoteProtocolError) as e:
                last_exc = e
                if attempt < self.MAX_RETRIES:
                    import time
                    time.sleep(1.0 * (attempt + 1))
                    continue
                raise
        raise last_exc  # type: ignore[misc]

    def get(self, url: str, **kwargs) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> httpx.Response:
        return self.request("POST", url, **kwargs)
