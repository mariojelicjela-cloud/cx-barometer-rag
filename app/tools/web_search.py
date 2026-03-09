import os
from tavily import TavilyClient


def tavily_search(query: str):

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        return [
            {
                "title": "Tavily unavailable",
                "url": "",
                "content": "TAVILY_API_KEY is not configured."
            }
        ]

    try:
        client = TavilyClient(api_key=api_key)

        response = client.search(
            query=query,
            search_depth="basic",
            max_results=5
        )

        results = []

        for item in response.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", "")
            })

        if len(results) == 0:
            return [{
                "title": "No public results",
                "url": "",
                "content": "No public web results were returned."
            }]

        return results

    except Exception as e:
        return [{
            "title": "Tavily error",
            "url": "",
            "content": f"Web search failed: {str(e)}"
        }]