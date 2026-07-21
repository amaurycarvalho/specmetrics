from __future__ import annotations

import re
from typing import Callable

from mcp.types import Prompt, ResourceTemplate, Tool


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._handlers: dict[str, Callable] = {}

    def register(self, tool: Tool, handler: Callable) -> None:
        self._tools[tool.name] = tool
        self._handlers[tool.name] = handler

    def get_tool(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def get_handler(self, name: str) -> Callable | None:
        return self._handlers.get(name)

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())


class ResourceRegistry:
    def __init__(self):
        self._templates: dict[str, ResourceTemplate] = {}
        self._handlers: dict[str, Callable] = {}
        self._patterns: dict[str, re.Pattern] = {}

    def register(self, template: ResourceTemplate, handler: Callable) -> None:
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

    def match_uri(self, uri: str) -> Callable | None:
        for template, handler in self._handlers.items():
            if self._patterns[template].match(uri):
                return handler
        return None

    def list_templates(self) -> list[ResourceTemplate]:
        return list(self._templates.values())


class PromptRegistry:
    def __init__(self):
        self._prompts: dict[str, Prompt] = {}

    def register(self, prompt: Prompt) -> None:
        self._prompts[prompt.name] = prompt

    def get_prompt(self, name: str) -> Prompt | None:
        return self._prompts.get(name)

    def list_prompts(self) -> list[Prompt]:
        return list(self._prompts.values())
