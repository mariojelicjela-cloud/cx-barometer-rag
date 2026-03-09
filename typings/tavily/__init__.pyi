from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class TavilySearchResult(TypedDict, total=False):
    title: str
    url: str
    content: str
    score: float


class TavilySearchResponse(TypedDict, total=False):
    query: str
    results: List[TavilySearchResult]


class TavilyClient:
    def __init__(self, api_key: Optional[str] = ...) -> None: ...
    def search(
        self,
        *,
        query: str,
        search_depth: str = ...,
        max_results: int = ...,
        **kwargs: Any,
    ) -> TavilySearchResponse: ...

