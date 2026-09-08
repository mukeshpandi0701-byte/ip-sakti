import json
from dataclasses import dataclass
from typing import Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.config import Settings
from app.knowledge_models import Evidence


@dataclass(frozen=True)
class GeneratedAnswer:
    answer: str
    provider: str
    grounded: bool
    confidence: float


class LLMService(Protocol):
    def generate_answer(self, query: str, evidence: list[Evidence]) -> GeneratedAnswer:
        """Generate an answer using only the supplied evidence."""


def build_grounded_prompt(query: str, evidence: list[Evidence]) -> str:
    evidence_text = "\n\n".join(
        f"Evidence [{item.chunk_id}]\n"
        f"Title: {item.title}\n"
        f"Source: {item.source}\n"
        f"Authority: {item.authority}\n"
        f"Excerpt: {item.excerpt}"
        for item in evidence
    )
    return f"""You are the IP-SAKTI grounded assistant.

Answer the user query ONLY from the supplied evidence.
Do not invent facts, laws, regulations, government sources, or citations.
Do not claim synthetic demo content is authoritative.
If the evidence is insufficient, say exactly that there is insufficient evidence to answer reliably.
Cite the evidence items used by their bracketed chunk IDs.

User query:
{query}

Supplied evidence:
{evidence_text}
"""


class FallbackLLMService:
    provider_name = "fallback-demo"

    def generate_answer(self, query: str, evidence: list[Evidence]) -> GeneratedAnswer:
        citations = ", ".join(f"[{item.chunk_id}]" for item in evidence)
        answer = (
            f"Demo grounded response for: {query}\n\n"
            "Based only on the supplied synthetic demo evidence, this is a planning-level "
            f"answer. Evidence used: {citations}.\n\n"
            "The evidence is synthetic and not authoritative legal or regulatory guidance."
        )
        return GeneratedAnswer(
            answer=answer,
            provider=self.provider_name,
            grounded=True,
            confidence=0.5,
        )


class OllamaLLMService:
    provider_name = "ollama"

    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.timeout_seconds = settings.ollama_timeout_seconds

    def generate_answer(self, query: str, evidence: list[Evidence]) -> GeneratedAnswer:
        payload = json.dumps(
            {
                "model": self.model,
                "prompt": build_grounded_prompt(query, evidence),
                "stream": False,
                "think": False,
            }
        ).encode("utf-8")
        request = Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError("Ollama is unavailable or returned invalid data") from exc

        answer = str(body.get("response", "")).strip()
        if not answer:
            raise RuntimeError("Ollama returned an empty answer")
        insufficient = "insufficient evidence" in answer.casefold()
        return GeneratedAnswer(
            answer=answer,
            provider=self.provider_name,
            grounded=not insufficient,
            confidence=0.8 if not insufficient else 0,
        )


def create_llm_service(settings: Settings) -> LLMService:
    if settings.llm_provider.casefold() == "ollama":
        return OllamaLLMService(settings)
    return FallbackLLMService()
