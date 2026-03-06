"""
Vision Tool
===========

Image analysis using GPT-4o vision capabilities.
"""

import base64
import aiohttp
from typing import Any, Dict, Optional
from aksi.tools.base import BaseTool, ToolResult
from aksi.config import settings


class VisionTool(BaseTool):
    """
    Vision tool for image analysis using GPT-4o.

    Supports base64 encoded images and URLs.
    """

    name = "vision"
    description = "Analyze images using GPT-4o vision model"

    def __init__(self):
        super().__init__()
        self.api_key = settings.openai_api_key
        self.model = settings.vision_model

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for vision parameters."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "image_base64": {
                        "type": "string",
                        "description": "Base64 encoded image data"
                    },
                    "image_url": {
                        "type": "string",
                        "description": "URL of the image to analyze"
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Analysis prompt/question about the image",
                        "default": "Describe this image in detail."
                    },
                    "detail": {
                        "type": "string",
                        "enum": ["low", "high", "auto"],
                        "description": "Image detail level",
                        "default": "auto"
                    }
                },
                "oneOf": [
                    {"required": ["image_base64"]},
                    {"required": ["image_url"]}
                ]
            }
        }

    async def execute(
        self,
        image_base64: Optional[str] = None,
        image_url: Optional[str] = None,
        prompt: str = "Describe this image in detail.",
        detail: str = "auto"
    ) -> ToolResult:
        """
        Analyze image using GPT-4o vision.

        Args:
            image_base64: Base64 encoded image data
            image_url: URL of image to analyze
            prompt: Analysis prompt
            detail: Detail level (low/high/auto)

        Returns:
            ToolResult with image analysis
        """
        if not self.api_key:
            return ToolResult(
                success=False,
                error="OpenAI API key not configured. Set AKSI_OPENAI_API_KEY"
            )

        if not image_base64 and not image_url:
            return ToolResult(
                success=False,
                error="Either image_base64 or image_url must be provided"
            )

        # Build image content
        if image_base64:
            # Detect image type from base64 header or default to jpeg
            image_type = self._detect_image_type(image_base64)
            image_content = {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{image_type};base64,{image_base64}",
                    "detail": detail
                }
            }
        else:
            image_content = {
                "type": "image_url",
                "image_url": {
                    "url": image_url,
                    "detail": detail
                }
            }

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    image_content
                ]
            }
        ]

        return await self._call_openai(messages, prompt)

    async def _call_openai(
        self,
        messages: list,
        prompt: str
    ) -> ToolResult:
        """Call OpenAI API for vision analysis."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1024
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        analysis = data["choices"][0]["message"]["content"]
                        return ToolResult(
                            success=True,
                            data={
                                "analysis": analysis,
                                "model": self.model,
                                "prompt": prompt
                            },
                            metadata={
                                "usage": data.get("usage", {}),
                                "model": data.get("model", "")
                            }
                        )
                    else:
                        error_text = await response.text()
                        return ToolResult(
                            success=False,
                            error=f"OpenAI API error: {response.status} - {error_text}"
                        )
        except aiohttp.ClientError as e:
            return ToolResult(
                success=False,
                error=f"Network error: {str(e)}"
            )

    def _detect_image_type(self, base64_data: str) -> str:
        """Detect image type from base64 data."""
        # Check for common image headers
        if base64_data.startswith("/9j/"):
            return "jpeg"
        elif base64_data.startswith("iVBORw0KGgo"):
            return "png"
        elif base64_data.startswith("R0lGOD"):
            return "gif"
        elif base64_data.startswith("UklGR"):
            return "webp"
        else:
            return "jpeg"  # Default to jpeg

    @staticmethod
    def encode_image_file(file_path: str) -> str:
        """
        Utility to encode image file to base64.

        Args:
            file_path: Path to image file

        Returns:
            Base64 encoded string
        """
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
