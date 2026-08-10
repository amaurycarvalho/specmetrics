"""Batch completion logic for the LLM gateway, provided as a mixin."""

from __future__ import annotations

import json
from typing import Any, Self

import structlog

from ._completion import build_json_instruction, detect_provider
from ._config import LLMGatewayConfig
from ._models import BatchRequest
from ._parsing import parse_batch_response

logger = structlog.get_logger(__name__)


class BatchMixin:
    """Provide the batched completion flow for the LLM gateway."""

    config: LLMGatewayConfig

    def complete_batch(
        self: Self, batch: BatchRequest, json_mode: bool = True
    ) -> dict[str, list[dict[str, Any]]]:
        """Complete a batch request, retrying failed documents individually."""
        sub_batches = batch.split(self.config.batch_max_chars)
        all_results: dict[str, list[dict[str, Any]]] = {}

        for sub_batch in sub_batches:
            provider = detect_provider(self.config.model)
            user_message = sub_batch.assemble_prompt()
            json_instruction = build_json_instruction(provider)
            system_prompt = sub_batch.system_prompt + json_instruction

            try:
                response_text = self.complete(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    json_mode=json_mode,
                )
                parsed = parse_batch_response(response_text, sub_batch)
                for doc_id, elements in parsed.items():
                    all_results.setdefault(doc_id, []).extend(elements)
            except (json.JSONDecodeError, ValueError, RuntimeError):
                logger.warning(
                    "batch_failed_retrying_individual",
                    doc_count=len(sub_batch.documents),
                )
                for doc in sub_batch.documents:
                    try:
                        single_prompt = f'Document "{doc.document_id}": {doc.content}'
                        response_text = self.complete(
                            system_prompt=system_prompt,
                            user_message=single_prompt,
                            json_mode=json_mode,
                        )
                        single_batch = BatchRequest(
                            system_prompt=sub_batch.system_prompt,
                            documents=[doc],
                            json_schema=sub_batch.json_schema,
                        )
                        parsed = parse_batch_response(response_text, single_batch)
                        all_results[doc.document_id] = parsed.get(doc.document_id, [])
                    except (json.JSONDecodeError, ValueError, RuntimeError):
                        logger.warning(
                            "individual_doc_failed",
                            doc_id=doc.document_id,
                        )
                        all_results[doc.document_id] = []

        return all_results