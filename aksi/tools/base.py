"""
Base Tool Class
===============

Abstract base class for all AKSI tools.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class ToolResult(BaseModel):
    """Result returned by a tool execution."""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class BaseTool(ABC):
    """Abstract base class for AKSI tools."""

    name: str = "base_tool"
    description: str = "Base tool class"

    def __init__(self):
        self.logger = logging.getLogger(f"aksi.tools.{self.name}")

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult with success status and data/error
        """
        pass

    def get_schema(self) -> Dict[str, Any]:
        """
        Return JSON schema for tool parameters.

        Returns:
            Dictionary describing tool parameters
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {}
        }

    def _log_execution(self, params: Dict[str, Any], result: ToolResult):
        """Log tool execution for debugging."""
        if result.success:
            self.logger.debug(f"Tool {self.name} executed successfully: {params}")
        else:
            self.logger.warning(f"Tool {self.name} failed: {result.error}")
