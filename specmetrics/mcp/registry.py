"""Registries for MCP tools, resources, and prompts."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Self

from mcp.types import Prompt, ResourceTemplate, Tool


class ToolRegistry:
    """Registry of MCP tools and their handlers."""

    def __init__(self: Self) -> None:
        """Initialize the registry with empty tool and handler maps."""
        self._tools: dict[str, Tool] = {}
        self._handlers: dict[str, Callable] = {}

    def register(self: Self, tool: Tool, handler: Callable) -> None:
        """Register a tool and its handler under the tool name."""
        self._tools[tool.name] = tool
        self._handlers[tool.name] = handler

    def get_tool(self: Self, name: str) -> Tool | None:
        """Return the tool definition for a name, or None."""
        return self._tools.get(name)

    def get_handler(self: Self, name: str) -> Callable | None:
        """Return the handler for a tool name, or None."""
        return self._handlers.get(name)

    def list_tools(self: Self) -> list[Tool]:
        """Return all registered tools."""
        return list(self._tools.values())


class ResourceRegistry:
    """Registry of MCP resource templates and their handlers."""

    def __init__(self: Self) -> None:
        """Initialize the registry with empty template maps."""
        self._templates: dict[str, ResourceTemplate] = {}
        self._handlers: dict[str, Callable] = {}
        self._patterns: dict[str, re.Pattern] = {}

    def register(self: Self, template: ResourceTemplate, handler: Callable) -> None:
        """Register a resource template and its handler."""
        self._templates[template.uriTemplate] = template
        self._handlers[template.uriTemplate] = handler
        pattern_str = (
            "^"
            + re.escape(template.uriTemplate)
            .replace(r"\{", "(?P<")
            .replace(r"\}", ">[^/]+)")
            + "$"
        )
        self._patterns[template.uriTemplate] = re.compile(pattern_str)

    def match_uri(self: Self, uri: str) -> Callable | None:
        """Return the handler whose template matches a URI, or None."""
        for template, handler in self._handlers.items():
            if self._patterns[template].match(uri):
                return handler
        return None

    def list_templates(self: Self) -> list[ResourceTemplate]:
        """Return all registered resource templates."""
        return list(self._templates.values())


class PromptRegistry:
    """Registry of MCP prompts."""

    def __init__(self: Self) -> None:
        """Initialize the registry with an empty prompt map."""
        self._prompts: dict[str, Prompt] = {}

    def register(self: Self, prompt: Prompt) -> None:
        """Register a prompt under its name."""
        self._prompts[prompt.name] = prompt

    def get_prompt(self: Self, name: str) -> Prompt | None:
        """Return the prompt for a name, or None."""
        return self._prompts.get(name)

    def list_prompts(self: Self) -> list[Prompt]:
        """Return all registered prompts."""
        return list(self._prompts.values())
