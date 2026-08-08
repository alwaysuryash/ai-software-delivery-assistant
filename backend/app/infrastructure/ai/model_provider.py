"""Model provider port and adapter (ADR-0001, BRD §14).

Decouples the orchestration layer from specific LLM clients. Provides an offline
fake model provider for reproducible, zero-cost development/testing.
"""

from __future__ import annotations

import abc
import json
from typing import Any
from app.core.config import Settings, get_settings


class ModelProvider(abc.ABC):
    """Port for AI chat completion models."""

    @abc.abstractmethod
    async def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        response_format: str | None = None,
        temperature: float = 0.0,
    ) -> str:
        """Call the swappable model provider."""


class FakeModelProvider(ModelProvider):
    """Deterministic mock adapter supporting offline mode."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        response_format: str | None = None,
        temperature: float = 0.0,
    ) -> str:
        # Determine agent type from prompts to return specialized responses
        prompt_lower = system_prompt.lower() + " " + user_prompt.lower()

        if "qa" in prompt_lower or "test" in prompt_lower:
            # QA Agent
            return json.dumps({
                "agent": "qa_agent",
                "status": "complete",
                "summary": "Critical test suite 'critical-regression' is blocked/unexecuted. One release-blocking critical defect is open.",
                "health": "red",
                "confidence": 0.95,
                "findings": [
                    {
                        "title": "Blocked critical regression suite execution",
                        "severity": "high",
                        "evidence": [{"source": "Test Management", "record_id": "TR-502", "retrieved_at": "2026-07-20T12:00:00Z"}],
                        "impact": "Release readiness is compromised — core retry and checkout paths remain unvalidated.",
                        "recommendation": "Unblock staging environment and rerun critical suite immediately.",
                        "owner": "QA Lead",
                        "due_date": "2026-07-24",
                    },
                    {
                        "title": "Open critical defect: BUG-77 Double charge on checkout retry",
                        "severity": "critical",
                        "evidence": [{"source": "WorkItem", "record_id": "BUG-77", "retrieved_at": "2026-07-20T12:00:00Z"}],
                        "impact": "Double charging users during payment retry violates basic business operations.",
                        "recommendation": "Fix bug BUG-77 and verify checkout flow.",
                        "owner": "Dev Lead",
                        "due_date": "2026-07-24",
                    }
                ],
                "data_gaps": [],
                "policy_flags": ["release_blocker_active"],
            })

        elif "dev" in prompt_lower or "repository" in prompt_lower or "pr" in prompt_lower:
            # Development Agent
            return json.dumps({
                "agent": "development_agent",
                "status": "complete",
                "summary": "Main build is currently failing. There is an open aged PR-311 (96 hours old) with no approvals.",
                "health": "red",
                "confidence": 0.9,
                "findings": [
                    {
                        "title": "Main pipeline build failure (ci-main)",
                        "severity": "high",
                        "evidence": [{"source": "Build", "record_id": "BUILD-889", "retrieved_at": "2026-07-20T12:00:00Z"}],
                        "impact": "Blocker for automatic deployments and signals trunk instability.",
                        "recommendation": "Inspect build logs for BUILD-889, revert breaking change or apply hotfix.",
                        "owner": "Dev Lead",
                        "due_date": "2026-07-21",
                    },
                    {
                        "title": "Aged open pull request (PR-311)",
                        "severity": "medium",
                        "evidence": [{"source": "PullRequest", "record_id": "PR-311", "retrieved_at": "2026-07-20T12:00:00Z"}],
                        "impact": "Code review delays delivery of Checkout payment retry logic.",
                        "recommendation": "Assign peer reviewer Sam to complete code review of PR-311.",
                        "owner": "Dana",
                        "due_date": "2026-07-22",
                    }
                ],
                "data_gaps": [],
                "policy_flags": ["build_failed"],
            })

        elif "ba" in prompt_lower or "requirement" in prompt_lower or "scope" in prompt_lower:
            # BA Agent
            return json.dumps({
                "agent": "ba_agent",
                "status": "complete",
                "summary": "Core requirements are missing acceptance criteria. refund policy is unrefined.",
                "health": "amber",
                "confidence": 0.85,
                "findings": [
                    {
                        "title": "Refund policy missing acceptance criteria",
                        "severity": "medium",
                        "evidence": [{"source": "WorkItem", "record_id": "WI-1004", "retrieved_at": "2026-07-20T12:00:00Z"}],
                        "impact": "Unrefined work item causes development ambiguity and delay.",
                        "recommendation": "Schedule refinement meeting with product owner to clarify acceptance criteria.",
                        "owner": "Business Analyst",
                        "due_date": "2026-07-22",
                    }
                ],
                "data_gaps": ["WI-1004 acceptance criteria"],
                "policy_flags": [],
            })

        elif "devops" in prompt_lower or "deployment" in prompt_lower or "pipeline" in prompt_lower:
            # DevOps Agent
            return json.dumps({
                "agent": "devops_agent",
                "status": "complete",
                "summary": "Staging environment is currently unavailable due to deployment failure. Rollback has not been validated.",
                "health": "red",
                "confidence": 0.9,
                "findings": [
                    {
                        "title": "Staging environment deployment failure",
                        "severity": "high",
                        "evidence": [{"source": "Deployment", "record_id": "DEP-070", "retrieved_at": "2026-07-20T12:00:00Z"}],
                        "impact": "Staging environment is offline; QA testing and stakeholder review are blocked.",
                        "recommendation": "Validate staging environment config and redeploy or rollback manually.",
                        "owner": "DevOps Lead",
                        "due_date": "2026-07-21",
                    }
                ],
                "data_gaps": [],
                "policy_flags": ["staging_offline"],
            })

        else:
            # PM Agent or default
            return json.dumps({
                "agent": "pm_agent",
                "status": "complete",
                "summary": "Overall sprint targets are at high risk. Overdue and blocked items are bottlenecking progress.",
                "health": "red",
                "confidence": 0.9,
                "findings": [
                    {
                        "title": "Blocked address validation story (WI-1002)",
                        "severity": "high",
                        "evidence": [{"source": "WorkItem", "record_id": "WI-1002", "retrieved_at": "2026-07-20T12:00:00Z"}],
                        "impact": "Sam is blocked, putting the Sprint 14 milestone scope at risk.",
                        "recommendation": "Resolve dependency with third-party address API.",
                        "owner": "PM",
                        "due_date": "2026-07-21",
                    },
                    {
                        "title": "Overdue cart persistence story (WI-1006)",
                        "severity": "medium",
                        "evidence": [{"source": "WorkItem", "record_id": "WI-1006", "retrieved_at": "2026-07-20T12:00:00Z"}],
                        "impact": "Aged story overdue by 1 day, reducing sprint velocity.",
                        "recommendation": "Reassign or swarm to close WI-1006.",
                        "owner": "Sam",
                        "due_date": "2026-07-21",
                    }
                ],
                "data_gaps": [],
                "policy_flags": ["schedule_risk"],
            })


class AzureOpenAIModelProvider(ModelProvider):
    """Live implementation for production (Azure OpenAI / AI Foundry)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        # Import dynamically so developers don't have to install openai if they only run fake
        try:
            from openai import AsyncAzureOpenAI
            self._client = AsyncAzureOpenAI(
                azure_endpoint=self.settings.azure_openai_endpoint,
                api_key=self.settings.azure_openai_api_key,
                api_version=self.settings.azure_openai_api_version,
            )
        except ImportError:
            self._client = None

    async def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        response_format: str | None = None,
        temperature: float = 0.0,
    ) -> str:
        if self._client is None:
            raise ImportError("The 'openai' package is required to use AzureOpenAIModelProvider.")

        kwargs: dict[str, Any] = {
            "model": self.settings.azure_openai_deployment,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }
        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}

        response = await self._client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""


def get_model_provider(settings: Settings | None = None) -> ModelProvider:
    settings = settings or get_settings()
    if settings.model_provider == "azure_openai":
        return AzureOpenAIModelProvider(settings)
    return FakeModelProvider(settings)
