import os
from typing import Optional
from ecommerce_ops_skill.http_client import BaseHttpClient


SERPAPI_BASE = "https://serpapi.com/search"


class WebSearchClient(BaseHttpClient):
    using_real_data = False

    def search_products(self, keyword: str, max_results: int = 10) -> dict:
        raise NotImplementedError

    def search_news(self, keyword: str, max_results: int = 10) -> dict:
        raise NotImplementedError

    def search_trends(self, keyword: str, max_results: int = 10) -> dict:
        raise NotImplementedError

    def _mock_results(self, keyword: str, count: int) -> list[dict]:
        return [
            {
                "title": f"{keyword} - 搜索结果 #{i+1}",
                "link": f"https://example.com/result/{i+1}",
                "snippet": f"关于{keyword}的相关信息，包括价格、评价和购买渠道。",
                "source": "example.com",
            }
            for i in range(count)
        ]


class SerpApiClient(WebSearchClient):
    BASE_URL = SERPAPI_BASE

    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self._api_key = api_key or os.environ.get("SERPAPI_API_KEY", "")
        if self._api_key:
            self.using_real_data = True

    def _search(self, keyword: str, tbm: str = "", max_results: int = 10) -> dict:
        if not self._api_key:
            return {
                "query": keyword,
                "results": self._mock_results(keyword, max_results),
                "total_results": max_results,
                "source_type": "mock",
                "using_real_data": False,
                "error": "SERPAPI_API_KEY 未设置，返回模拟数据",
            }

        params = {
            "api_key": self._api_key,
            "q": keyword,
            "num": min(max_results, 20),
            "engine": "google",
            "gl": "cn",
            "hl": "zh-cn",
        }
        if tbm:
            params["tbm"] = tbm
        try:
            resp = self.get(SERPAPI_BASE, params=params)
            data = resp.json()
            results = []
            for item in data.get("organic_results", [])[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": item.get("source", ""),
                })
            return {
                "query": keyword,
                "results": results,
                "total_results": len(results),
                "source_type": "serpapi",
                "using_real_data": True,
            }
        except Exception as e:
            return {
                "query": keyword,
                "results": self._mock_results(keyword, max_results),
                "total_results": max_results,
                "source_type": "mock",
                "using_real_data": False,
                "error": str(e),
            }

    def search_products(self, keyword: str, max_results: int = 10) -> dict:
        result = self._search(keyword, tbm="shop", max_results=max_results)
        if result["using_real_data"]:
            result["result_type"] = "shopping"
        return result

    def search_news(self, keyword: str, max_results: int = 10) -> dict:
        result = self._search(keyword, tbm="nws", max_results=max_results)
        if result["using_real_data"]:
            result["result_type"] = "news"
        return result

    def search_trends(self, keyword: str, max_results: int = 10) -> dict:
        result = self._search(keyword, max_results=max_results)
        if result["using_real_data"]:
            result["result_type"] = "trends"
        return result


class MockWebSearchClient(WebSearchClient):
    using_real_data = False

    def search_products(self, keyword: str, max_results: int = 10) -> dict:
        return {
            "query": keyword,
            "results": self._mock_results(keyword, max_results),
            "total_results": max_results,
            "source_type": "mock",
            "result_type": "shopping",
            "using_real_data": False,
        }

    def search_news(self, keyword: str, max_results: int = 10) -> dict:
        return {
            "query": keyword,
            "results": self._mock_results(keyword, max_results),
            "total_results": max_results,
            "source_type": "mock",
            "result_type": "news",
            "using_real_data": False,
        }

    def search_trends(self, keyword: str, max_results: int = 10) -> dict:
        return {
            "query": keyword,
            "results": self._mock_results(keyword, max_results),
            "total_results": max_results,
            "source_type": "mock",
            "result_type": "trends",
            "using_real_data": False,
        }
