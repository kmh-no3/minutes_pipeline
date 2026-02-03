from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from .prompt import extract_json


class Summarizer(Protocol):
    def summarize(self, system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
        ...


@dataclass
class MockSummarizer:
    def summarize(self, system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
        minutes = {
            "meeting": {"title": "（自動生成）", "date": "", "participants": []},
            "summary": ["（モック要約）LLMを有効化すると精度が上がります。"],
            "decisions": [],
            "todos": [
                {"owner": "", "task": "summarize.engine を manual または API/ollama に切り替える。", "due": ""}
            ],
            "topics": [],
            "open_questions": [],
            "next_steps": [],
            "notes": "",
        }
        return json.dumps(minutes, ensure_ascii=False)


@dataclass
class OpenAISummarizer:
    def summarize(self, system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as e:
            raise RuntimeError("openai not installed. pip install -e '.[openai]'") from e
        client = OpenAI()
        mdl = model or "gpt-4o-mini"
        resp = client.chat.completions.create(
            model=mdl,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content or ""


@dataclass
class AnthropicSummarizer:
    def summarize(self, system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
        try:
            import anthropic  # type: ignore
        except ImportError as e:
            raise RuntimeError("anthropic not installed. pip install -e '.[anthropic]'") from e
        client = anthropic.Anthropic()
        mdl = model or "claude-3-5-sonnet-latest"
        msg = client.messages.create(
            model=mdl,
            max_tokens=1500,
            temperature=0.2,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        parts = []
        for block in msg.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        return "\n".join(parts).strip()


@dataclass
class OllamaSummarizer:
    base_url: str = "http://localhost:11434"

    def summarize(self, system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
        try:
            import httpx  # type: ignore
        except ImportError as e:
            raise RuntimeError("httpx not installed. pip install -e '.[ollama]'") from e
        mdl = model or "llama3.1"
        payload = {
            "model": mdl,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.2},
        }
        url = self.base_url.rstrip("/") + "/api/chat"
        with httpx.Client(timeout=180.0) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
        return (data.get("message", {}) or {}).get("content", "") or ""


def get_summarizer(engine: str, ollama_base_url: str = "http://localhost:11434") -> Summarizer:
    e = (engine or "mock").lower()
    if e == "mock":
        return MockSummarizer()
    if e == "openai":
        return OpenAISummarizer()
    if e == "anthropic":
        return AnthropicSummarizer()
    if e == "ollama":
        return OllamaSummarizer(base_url=ollama_base_url)
    raise ValueError(f"Unknown summarize.engine: {engine}")


def run_llm_and_parse_json(
    summarizer: Summarizer,
    system_prompt: str,
    user_prompt: str,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    raw = summarizer.summarize(system_prompt=system_prompt, user_prompt=user_prompt, model=model)
    return extract_json(raw)
