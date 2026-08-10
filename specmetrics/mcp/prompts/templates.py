"""Static prompt templates exposed by the MCP server."""

from __future__ import annotations

from mcp.types import Prompt, PromptArgument

MEASURE_PROJECT_PROMPT = Prompt(
    name="measure_project",
    description="Guide to measure a specification project through the full pipeline",
    arguments=[
        PromptArgument(
            name="project_path",
            description="Path to the SpecMetrics project directory",
            required=True,
        ),
        PromptArgument(
            name="export_format",
            description="Export format for results (json or csv)",
            required=False,
        ),
    ],
)

ANALYZE_SPEC_PROMPT = Prompt(
    name="analyze_spec",
    description="Guide to read and analyze a specification document",
    arguments=[
        PromptArgument(
            name="spec_path",
            description="Path to the specification file",
            required=True,
        ),
    ],
)

EXPORT_RESULTS_PROMPT = Prompt(
    name="export_results",
    description="Guide to export measurement results from a completed pipeline run",
    arguments=[
        PromptArgument(
            name="project_path",
            description="Path to the SpecMetrics project",
            required=True,
        ),
        PromptArgument(
            name="format",
            description="Export format (json or csv)",
            required=True,
        ),
    ],
)
