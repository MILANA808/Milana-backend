"""
Web Search Tool
===============

Real-time web search integration using Tavily or Serper API.
"""

import aiohttp
from typing import Any, Dict, List, Optional
from aksi.tools.base import BaseTool, ToolResult
from aksi.config import settings


class WebSearchTool(BaseTool):
    """
    Web search tool using Tavily or Serper API.

    Supports both providers with automatic fallback.
    """

    name = "web_search"
    description = "Search the internet for real-time information"

    def __init__(self):
        super().__init__()
        self.tavily_api_key = settings.tavily_api_key
        self.serper_api_key = settings.serper_api_key

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for web search parameters."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 5
                    },
                    "search_depth": {
                        "type": "string",
                        "enum": ["basic", "advanced"],
                        "description": "Search depth level",
                        "default": "basic"
                    }
                },
                "required": ["query"]
            }
        }

    async def execute(
        self,
        query: str,
        num_results: int = 5,
        search_depth: str = "basic"
    ) -> ToolResult:
        """
        Execute web search.

        Args:
            query: Search query string
            num_results: Number of results to return
            search_depth: 'basic' or 'advanced' search

        Returns:
            ToolResult with search results
        """
        # Try Tavily first, then Serper
        if self.tavily_api_key:
            return await self._search_tavily(query, num_results, search_depth)
        elif self.serper_api_key:
            return await self._search_serper(query, num_results)
        else:
            return ToolResult(
                success=False,
                error="No search API key configured. Set AKSI_TAVILY_API_KEY or AKSI_SERPER_API_KEY"
            )

    async def _search_tavily(
        self,
        query: str,
        num_results: int,
        search_depth: str
    ) -> ToolResult:
        """Search using Tavily API."""
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": search_depth,
            "max_results": num_results,
            "include_answer": True,
            "include_raw_content": False
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = self._format_tavily_results(data)
                        return ToolResult(
                            success=True,
                            data=results,
                            metadata={
                                "provider": "tavily",
                                "query": query,
                                "num_results": len(results.get("results", []))
                            }
                        )
                    else:
                        error_text = await response.text()
                        return ToolResult(
                            success=False,
                            error=f"Tavily API error: {response.status} - {error_text}"
                        )
        except aiohttp.ClientError as e:
            return ToolResult(
                success=False,
                error=f"Network error: {str(e)}"
            )

    async def _search_serper(self, query: str, num_results: int) -> ToolResult:
        """Search using Serper API."""
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": self.serper_api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "q": query,
            "num": num_results
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = self._format_serper_results(data)
                        return ToolResult(
                            success=True,
                            data=results,
                            metadata={
                                "provider": "serper",
                                "query": query,
                                "num_results": len(results.get("results", []))
                            }
                        )
                    else:
                        error_text = await response.text()
                        return ToolResult(
                            success=False,
                            error=f"Serper API error: {response.status} - {error_text}"
                        )
        except aiohttp.ClientError as e:
            return ToolResult(
                success=False,
                error=f"Network error: {str(e)}"
            )

    def _format_tavily_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format Tavily API response."""
        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "score": item.get("score", 0)
            })

        return {
            "answer": data.get("answer", ""),
            "results": results,
            "query": data.get("query", "")
        }

    def _format_serper_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format Serper API response."""
        results = []
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "content": item.get("snippet", ""),
                "position": item.get("position", 0)
            })

        return {
            "answer": data.get("answerBox", {}).get("answer", ""),
            "results": results,
            "query": data.get("searchParameters", {}).get("q", "")
        }
