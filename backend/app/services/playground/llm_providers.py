"""Unified LLM provider abstraction for the Agent Simulator Playground.

Supports OpenAI, Google Gemini (AI Studio), Google Gemini (Vertex AI ADC),
Ollama, Azure OpenAI, and Anthropic Claude. Each provider implements a single
method:

    async chat_completion(system_prompt: str, messages: list, json_mode: bool) -> dict

Returns a standardized dict::

    {
        "content": "...",           # Raw text response
        "structured": {...} | None, # Parsed JSON if json_mode=True
        "model": "...",
        "provider": "...",
        "latency_ms": float,
    }
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx

from app.core.config import get_settings


class LLMResponse:
    """Standardized response across all LLM providers."""

    def __init__(
        self,
        content: str,
        structured: Optional[dict] = None,
        model: str = "unknown",
        provider: str = "unknown",
        latency_ms: float = 0.0,
        error: Optional[str] = None,
    ):
        self.content = content
        self.structured = structured
        self.model = model
        self.provider = provider
        self.latency_ms = latency_ms
        self.error = error


class BaseLLMProvider(ABC):
    """Abstract base for all LLM providers."""

    name: str = "base"

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def chat_completion(
        self,
        system_prompt: str,
        messages: list[dict],
        json_mode: bool = False,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Call the LLM and return a standardized response."""
        ...

    @abstractmethod
    async def list_models(self) -> list[dict]:
        """Return a list of available models for this provider.

        Each model is a dict with ``id`` and ``name`` keys.
        """
        ...

    def _build_json_instructions(self) -> str:
        return (
            "\n\nIMPORTANT: Respond ONLY with a valid JSON object. "
            "No markdown, no explanations outside the JSON."
        )


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT-4 / GPT-3.5 provider."""

    name = "openai"

    async def list_models(self) -> list[dict]:
        api_key = self.config.get("api_key") or os.environ.get("OPENAI_API_KEY")
        base_url = self.config.get("base_url") or "https://api.openai.com/v1"
        if not api_key:
            return []
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(f"{base_url}/models", headers=headers)
                resp.raise_for_status()
                data = resp.json()
                models = []
                for m in data.get("data", []):
                    model_id = m.get("id", "")
                    # Filter for GPT-family models
                    if model_id.startswith("gpt-"):
                        models.append({"id": model_id, "name": model_id.replace("-", " ").upper()})
                # Sort by id for stable ordering
                models.sort(key=lambda x: x["id"])
                return models
        except Exception:
            return []

    async def chat_completion(
        self,
        system_prompt: str,
        messages: list[dict],
        json_mode: bool = False,
        temperature: float = 0.7,
    ) -> LLMResponse:
        api_key = self.config.get("api_key") or os.environ.get("OPENAI_API_KEY")
        base_url = self.config.get("base_url") or "https://api.openai.com/v1"
        model = self.config.get("model") or "gpt-4o-mini"

        if not api_key:
            return LLMResponse(content="", error="OpenAI API key not configured", provider=self.name)

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload: dict[str, Any] = {
            "model": model,
            "temperature": temperature,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
            payload["messages"][0]["content"] += self._build_json_instructions()

        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                structured = None
                if json_mode:
                    try:
                        structured = json.loads(content)
                    except json.JSONDecodeError:
                        pass
                return LLMResponse(
                    content=content,
                    structured=structured,
                    model=model,
                    provider=self.name,
                    latency_ms=(time.time() - start) * 1000,
                )
        except Exception as exc:
            return LLMResponse(content="", error=str(exc), provider=self.name, latency_ms=(time.time() - start) * 1000)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini (AI Studio or Vertex AI via ADC)."""

    name = "gemini"

    async def list_models(self) -> list[dict]:
        return [
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash"},
            {"id": "gemini-1.5-flash-8b", "name": "Gemini 1.5 Flash 8B"},
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro"},
            {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash"},
            {"id": "gemini-2.0-pro-exp-02-05", "name": "Gemini 2.0 Pro Experimental"},
        ]

    async def chat_completion(
        self,
        system_prompt: str,
        messages: list[dict],
        json_mode: bool = False,
        temperature: float = 0.7,
    ) -> LLMResponse:
        api_key = self.config.get("api_key") or os.environ.get("GEMINI_API_KEY")
        model = self.config.get("model") or "gemini-1.5-flash"

        if not api_key:
            # Try Vertex AI ADC fallback
            try:
                import google.auth
                import google.generativeai as genai

                credentials, project = google.auth.default()
                genai.configure(credentials=credentials, project=project)
            except Exception as exc:
                return LLMResponse(content="", error=f"Gemini API key not configured and ADC failed: {exc}", provider=self.name)
        else:
            try:
                import google.generativeai as genai

                genai.configure(api_key=api_key)
            except Exception as exc:
                return LLMResponse(content="", error=str(exc), provider=self.name)

        try:
            import google.generativeai as genai
        except ImportError:
            return LLMResponse(content="", error="google-generativeai not installed", provider=self.name)

        genai_model = genai.GenerativeModel(model)
        contents = []
        for m in messages:
            role = m.get("role", "user")
            text = m.get("content", "")
            if role == "user":
                contents.append({"role": "user", "parts": [text]})
            else:
                contents.append({"role": "model", "parts": [text]})

        prompt = system_prompt + "\n\n" + "\n".join(m.get("content", "") for m in messages)
        if json_mode:
            prompt += self._build_json_instructions()

        generation_config = {"temperature": temperature}
        if json_mode:
            generation_config["response_mime_type"] = "application/json"

        start = time.time()
        try:
            response = await genai_model.generate_content_async(
                prompt,
                generation_config=genai.GenerationConfig(**generation_config),
            )
            text = response.text.strip()
            structured = None
            if json_mode:
                try:
                    structured = json.loads(text)
                except json.JSONDecodeError:
                    pass
            return LLMResponse(
                content=text,
                structured=structured,
                model=model,
                provider=self.name,
                latency_ms=(time.time() - start) * 1000,
            )
        except Exception as exc:
            return LLMResponse(content="", error=str(exc), provider=self.name, latency_ms=(time.time() - start) * 1000)


class OllamaProvider(BaseLLMProvider):
    """Local Ollama provider."""

    name = "ollama"

    async def list_models(self) -> list[dict]:
        base_url = self.config.get("base_url") or "http://localhost:11434"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(f"{base_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                models = []
                for m in data.get("models", []):
                    model_id = m.get("name", "")
                    if model_id:
                        models.append({"id": model_id, "name": model_id})
                return models
        except Exception:
            return []

    async def chat_completion(
        self,
        system_prompt: str,
        messages: list[dict],
        json_mode: bool = False,
        temperature: float = 0.7,
    ) -> LLMResponse:
        base_url = self.config.get("base_url") or "http://localhost:11434"
        model = self.config.get("model") or "llama3.1"

        payload = {
            "model": model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if json_mode:
            payload["format"] = "json"
            payload["messages"][0]["content"] += self._build_json_instructions()

        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{base_url}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
                content = data["message"]["content"]
                structured = None
                if json_mode:
                    try:
                        structured = json.loads(content)
                    except json.JSONDecodeError:
                        pass
                return LLMResponse(
                    content=content,
                    structured=structured,
                    model=model,
                    provider=self.name,
                    latency_ms=(time.time() - start) * 1000,
                )
        except Exception as exc:
            return LLMResponse(content="", error=str(exc), provider=self.name, latency_ms=(time.time() - start) * 1000)


class OllamaCloudProvider(BaseLLMProvider):
    """Ollama Cloud provider (remote Ollama instances with API key)."""

    name = "ollama_cloud"

    async def list_models(self) -> list[dict]:
        base_url = self.config.get("base_url") or "https://api.ollama.com"
        api_key = self.config.get("api_key") or os.environ.get("OLLAMA_CLOUD_API_KEY")
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(f"{base_url}/api/tags", headers=headers)
                resp.raise_for_status()
                data = resp.json()
                models = []
                for m in data.get("models", []):
                    model_id = m.get("name", "")
                    if model_id:
                        models.append({"id": model_id, "name": model_id})
                return models
        except Exception:
            return []

    async def chat_completion(
        self,
        system_prompt: str,
        messages: list[dict],
        json_mode: bool = False,
        temperature: float = 0.7,
    ) -> LLMResponse:
        base_url = self.config.get("base_url") or "https://api.ollama.com"
        model = self.config.get("model") or "llama3.1"
        api_key = self.config.get("api_key") or os.environ.get("OLLAMA_CLOUD_API_KEY")

        if not api_key:
            return LLMResponse(content="", error="Ollama Cloud API key not configured", provider=self.name)

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if json_mode:
            payload["format"] = "json"
            payload["messages"][0]["content"] += self._build_json_instructions()

        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{base_url}/api/chat", headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                content = data["message"]["content"]
                structured = None
                if json_mode:
                    try:
                        structured = json.loads(content)
                    except json.JSONDecodeError:
                        pass
                return LLMResponse(
                    content=content,
                    structured=structured,
                    model=model,
                    provider=self.name,
                    latency_ms=(time.time() - start) * 1000,
                )
        except Exception as exc:
            return LLMResponse(content="", error=str(exc), provider=self.name, latency_ms=(time.time() - start) * 1000)


class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI Service provider."""

    name = "azure_openai"

    async def list_models(self) -> list[dict]:
        # Azure does not expose a simple unauthenticated models list API.
        return []

    async def chat_completion(
        self,
        system_prompt: str,
        messages: list[dict],
        json_mode: bool = False,
        temperature: float = 0.7,
    ) -> LLMResponse:
        api_key = self.config.get("api_key") or os.environ.get("AZURE_OPENAI_API_KEY")
        endpoint = self.config.get("endpoint") or os.environ.get("AZURE_OPENAI_ENDPOINT")
        deployment = self.config.get("deployment") or "gpt-4"
        api_version = self.config.get("api_version", "2024-02-01")

        if not api_key or not endpoint:
            return LLMResponse(content="", error="Azure OpenAI API key or endpoint not configured", provider=self.name)

        headers = {"api-key": api_key, "Content-Type": "application/json"}
        payload: dict[str, Any] = {
            "temperature": temperature,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
            payload["messages"][0]["content"] += self._build_json_instructions()

        url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                structured = None
                if json_mode:
                    try:
                        structured = json.loads(content)
                    except json.JSONDecodeError:
                        pass
                return LLMResponse(
                    content=content,
                    structured=structured,
                    model=deployment,
                    provider=self.name,
                    latency_ms=(time.time() - start) * 1000,
                )
        except Exception as exc:
            return LLMResponse(content="", error=str(exc), provider=self.name, latency_ms=(time.time() - start) * 1000)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider."""

    name = "anthropic"

    async def list_models(self) -> list[dict]:
        return [
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet"},
            {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku"},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus"},
            {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet"},
            {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku"},
        ]

    async def chat_completion(
        self,
        system_prompt: str,
        messages: list[dict],
        json_mode: bool = False,
        temperature: float = 0.7,
    ) -> LLMResponse:
        api_key = self.config.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        model = self.config.get("model") or "claude-3-5-sonnet-20241022"

        if not api_key:
            return LLMResponse(content="", error="Anthropic API key not configured", provider=self.name)

        headers = {"x-api-key": api_key, "Content-Type": "application/json", "anthropic-version": "2023-06-01"}
        payload = {
            "model": model,
            "max_tokens": 1024,
            "temperature": temperature,
            "system": system_prompt,
            "messages": messages,
        }
        if json_mode:
            payload["system"] += self._build_json_instructions()

        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                content = data["content"][0]["text"]
                structured = None
                if json_mode:
                    try:
                        structured = json.loads(content)
                    except json.JSONDecodeError:
                        pass
                return LLMResponse(
                    content=content,
                    structured=structured,
                    model=model,
                    provider=self.name,
                    latency_ms=(time.time() - start) * 1000,
                )
        except Exception as exc:
            return LLMResponse(content="", error=str(exc), provider=self.name, latency_ms=(time.time() - start) * 1000)


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

class GeminiADCProvider(BaseLLMProvider):
    """Google Gemini via Vertex AI using Application Default Credentials (ADC).

    Uses the Google Gen AI SDK (google-genai) with vertexai=True and the
    global endpoint, matching the Agent Platform / Gemini Cloud Assist setup.
    """

    name = "gemini_adc"

    async def list_models(self) -> list[dict]:
        project = self.config.get("project_id") or get_settings().gcp_project_id
        location = self.config.get("location") or get_settings().gcp_location or "global"

        if not project:
            return []

        try:
            from google import genai
        except ImportError:
            return []

        try:
            client = genai.Client(vertexai=True, project=project, location=location)
            models = []
            for m in client.models.list():
                name = m.name or ""
                # Strip publishers/google/models/ prefix
                if name.startswith("publishers/google/models/"):
                    model_id = name.replace("publishers/google/models/", "")
                else:
                    model_id = name
                # Skip non-Gemini models and embedding models
                if not model_id.startswith("gemini-"):
                    continue
                # Build a friendly display name
                display = model_id.replace("-", " ").title()
                models.append({"id": model_id, "name": display})
            return models
        except Exception:
            # Fallback to hardcoded list if API fails
            return [
                {"id": "gemini-2.5-flash-lite-preview-09-2025", "name": "Gemini 2.5 Flash-Lite Preview"},
                {"id": "gemini-2.5-pro-preview-03-25", "name": "Gemini 2.5 Pro Preview"},
                {"id": "gemini-2.0-flash-001", "name": "Gemini 2.0 Flash"},
                {"id": "gemini-2.0-pro-001", "name": "Gemini 2.0 Pro"},
                {"id": "gemini-1.5-flash-002", "name": "Gemini 1.5 Flash"},
                {"id": "gemini-1.5-pro-002", "name": "Gemini 1.5 Pro"},
            ]

    async def chat_completion(
        self,
        system_prompt: str,
        messages: list[dict],
        json_mode: bool = False,
        temperature: float = 0.7,
    ) -> LLMResponse:
        model = self.config.get("model") or "gemini-2.5-flash-lite-preview-09-2025"
        project = self.config.get("project_id") or get_settings().gcp_project_id
        location = self.config.get("location") or get_settings().gcp_location or "global"

        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            return LLMResponse(
                content="",
                error=f"google-genai not installed: {exc}",
                provider=self.name,
            )

        if not project:
            return LLMResponse(
                content="",
                error="No GCP project_id configured. Set it in the provider config or in GCP_PROJECT_ID env var.",
                provider=self.name,
            )

        start = time.time()
        try:
            def _call():
                client = genai.Client(vertexai=True, project=project, location=location)
                prompt = system_prompt + "\n\n" + "\n".join(m.get("content", "") for m in messages)
                if json_mode:
                    prompt += self._build_json_instructions()

                config = types.GenerateContentConfig(temperature=temperature)
                if json_mode:
                    config.response_mime_type = "application/json"

                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )
                return response.text or ""

            text = await asyncio.to_thread(_call)
            structured = None
            if json_mode:
                try:
                    structured = json.loads(text)
                except json.JSONDecodeError:
                    pass
            return LLMResponse(
                content=text,
                structured=structured,
                model=model,
                provider=self.name,
                latency_ms=(time.time() - start) * 1000,
            )
        except Exception as exc:
            return LLMResponse(content="", error=str(exc), provider=self.name, latency_ms=(time.time() - start) * 1000)


_PROVIDER_MAP: dict[str, type[BaseLLMProvider]] = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "ollama": OllamaProvider,
    "ollama_cloud": OllamaCloudProvider,
    "azure_openai": AzureOpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini_adc": GeminiADCProvider,
}


class LLMProviderFactory:
    """Factory to instantiate the correct LLM provider."""

    @staticmethod
    def create(provider_name: str, config: dict) -> BaseLLMProvider:
        cls = _PROVIDER_MAP.get(provider_name)
        if not cls:
            raise ValueError(f"Unknown LLM provider: {provider_name}. Available: {list(_PROVIDER_MAP.keys())}")
        return cls(config)

    @staticmethod
    def list_providers() -> list[dict]:
        """Return metadata about all supported providers."""
        return [
            {
                "name": "openai",
                "display_name": "OpenAI",
                "description": "GPT-4, GPT-3.5, GPT-4o via OpenAI API",
                "requires_api_key": True,
                "default_model": "gpt-4o-mini",
                "configurable_fields": ["api_key", "base_url", "model"],
            },
            {
                "name": "gemini",
                "display_name": "Google Gemini",
                "description": "Gemini Flash/Pro via AI Studio or Vertex AI ADC",
                "requires_api_key": True,
                "default_model": "gemini-1.5-flash",
                "configurable_fields": ["api_key", "model"],
            },
            {
                "name": "ollama",
                "display_name": "Ollama (Local)",
                "description": "Run local models via Ollama (Llama, Mistral, etc.)",
                "requires_api_key": False,
                "default_model": "llama3.1",
                "configurable_fields": ["base_url", "model"],
            },
            {
                "name": "ollama_cloud",
                "display_name": "Ollama Cloud",
                "description": "Remote Ollama instances via Ollama Cloud API (requires API key)",
                "requires_api_key": True,
                "default_model": "llama3.1",
                "configurable_fields": ["api_key", "base_url", "model"],
            },
            {
                "name": "azure_openai",
                "display_name": "Azure OpenAI",
                "description": "Enterprise OpenAI via Azure Cognitive Services",
                "requires_api_key": True,
                "default_model": "gpt-4",
                "configurable_fields": ["api_key", "endpoint", "deployment", "api_version"],
            },
            {
                "name": "anthropic",
                "display_name": "Anthropic Claude",
                "description": "Claude 3.5 Sonnet, Claude 3 Opus via Anthropic API",
                "requires_api_key": True,
                "default_model": "claude-3-5-sonnet-20241022",
                "configurable_fields": ["api_key", "model"],
            },
            {
                "name": "gemini_adc",
                "display_name": "Google Gemini (Vertex ADC)",
                "description": "Gemini via Vertex AI using Application Default Credentials (gcloud auth, service account, etc.)",
                "requires_api_key": False,
                "default_model": "gemini-2.5-flash-lite-preview-09-2025",
                "configurable_fields": ["project_id", "location", "model"],
            },
        ]


def get_available_providers() -> list[dict]:
    return LLMProviderFactory.list_providers()
