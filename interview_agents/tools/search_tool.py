from __future__ import annotations

import json
from typing import Any

import requests
from requests import RequestException

from interview_agents.config.settings import settings


class SearchTool:
    """Tavily-backed search helper with a graceful fallback message."""

    def search(self, query: str, max_results: int = 5) -> str:
        if not settings.tavily_api_key or settings.tavily_api_key.lower().startswith("your_"):
            return "No search API configured (set TAVILY_API_KEY)."

        try:
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.tavily_api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "advanced",
                },
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
        except RequestException as exc:
            return f"Search unavailable ({exc}). Continue without web research."

        results: list[dict[str, Any]] = payload.get("results", [])
        compact = []
        for r in results:
            compact.append(
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                }
            )
        return json.dumps(compact, ensure_ascii=True, indent=2)
