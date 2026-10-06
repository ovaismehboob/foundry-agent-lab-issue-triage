"""Foundry IQ knowledge base integration (Module 5).

Uses the Agent Framework Azure AI Search context provider in *agentic* mode against the
knowledge base created in the Foundry portal in Module 4. Before each model call, the provider
retrieves knowledge and adds it to the model context.

This module only records the citation annotations that the service actually returns, so the CLI
can show them. It never creates or guesses citations.
"""

from __future__ import annotations

from typing import Any

from triage_desk.config import Settings

KNOWLEDGE_SOURCE_ID = "foundry_iq"


def build_knowledge_provider(settings: Settings, credential: Any) -> Any:
    from agent_framework.azure import AzureAISearchContextProvider

    class CitationCapturingProvider(AzureAISearchContextProvider):
        """Records the references returned by the knowledge base for the most recent request.

        `last_references` is per provider instance. That is fine for the single-user CLI; a
        multi-user service should read references from the per-request context instead.
        """

        last_references: list[dict]

        async def before_run(self, *, agent: Any, session: Any, context: Any, state: dict) -> None:
            self.last_references = []
            await super().before_run(agent=agent, session=session, context=context, state=state)
            references: list[dict] = []
            seen: set[tuple] = set()
            for message in context.get_messages(sources={self.source_id}):
                for content in getattr(message, "contents", None) or []:
                    for annotation in getattr(content, "annotations", None) or []:
                        if not hasattr(annotation, "get"):
                            continue
                        extra = annotation.get("additional_properties") or {}
                        source_data = extra.get("source_data") or {}
                        if not isinstance(source_data, dict):
                            source_data = {}
                        # Prefer the document path/title the service returns; fall back to the reference ID.
                        title = (
                            source_data.get("metadata_storage_path")
                            or source_data.get("title")
                            or annotation.get("title")
                        )
                        url = annotation.get("url") or None
                        key = (title, url)  # One line per document, even when several chunks matched.
                        if key in seen:
                            continue
                        seen.add(key)
                        references.append(
                            {
                                "title": title,
                                "url": url,
                                "reference_id": extra.get("reference_id"),
                                "reranker_score": extra.get("reranker_score"),
                            }
                        )
            self.last_references = references

    provider = CitationCapturingProvider(
        source_id=KNOWLEDGE_SOURCE_ID,
        endpoint=settings.search_endpoint,
        credential=credential,
        mode="agentic",
        knowledge_base_name=settings.knowledge_base_name,
        knowledge_base_output_mode="extractive_data",
        retrieval_reasoning_effort="minimal",
    )
    provider.last_references = []
    return provider


def references_from(agent: Any) -> list[dict]:
    """Return the references captured by the agent's knowledge provider, if any."""
    for provider in getattr(agent, "context_providers", None) or []:
        if hasattr(provider, "last_references"):
            return list(provider.last_references)
    return []


async def close_providers(agent: Any) -> None:
    """Close network sessions opened by context providers (call when the agent is no longer needed)."""
    for provider in getattr(agent, "context_providers", None) or []:
        close = getattr(provider, "close", None)
        if close is not None:
            try:
                await close()
            except Exception:  # Closing is best effort; never hide the real result.
                pass
