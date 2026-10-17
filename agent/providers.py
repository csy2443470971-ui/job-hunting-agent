"""Model providers. Every node asks for structured output through one call:

    structured(system_blocks, user_text, Schema, effort="medium", max_tokens=8000) -> Schema instance

Pick a provider with LLM_PROVIDER in .env:
  anthropic    Claude via the Anthropic API (default). ANTHROPIC_API_KEY, MODEL_TAILOR / MODEL_SCORE.
  openai_compat  Any OpenAI-compatible endpoint: Ollama, vLLM, LM Studio, llama.cpp server, OpenRouter.
               LLM_BASE_URL (e.g. http://localhost:11434/v1), LLM_MODEL (e.g. qwen3:32b), LLM_API_KEY (optional).
  claude_code  The local `claude` CLI in headless mode. Uses your Claude Code login; no API key.

Relevance ranking has its own provider (agent/jev.py, TypeSafe Jev) with a keyword fallback.
"""
from __future__ import annotations
import json
import os
import re
import subprocess
from typing import Type, TypeVar
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


def _flatten(system_blocks: list[dict]) -> str:
    return "\n\n".join(b["text"] for b in system_blocks)


def _extract_json(text: str) -> str:
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if m:
        return m.group(1)
    a, b = text.find("{"), text.rfind("}")
    return text[a:b + 1] if a >= 0 else text


def _anthropic(system_blocks, user, schema: Type[T], effort, max_tokens, model) -> T:
    import anthropic
    client = anthropic.Anthropic()
    if max_tokens > 8000:
        with client.messages.stream(model=model, max_tokens=max_tokens, output_config={"effort": effort},
                                    system=system_blocks, messages=[{"role": "user", "content": user}], output_format=schema) as s:
            return s.get_final_message().parsed_output
    r = client.messages.parse(model=model, max_tokens=max_tokens, output_config={"effort": effort},
                              system=system_blocks, messages=[{"role": "user", "content": user}], output_format=schema)
    return r.parsed_output


def _openai_compat(system_blocks, user, schema: Type[T], effort, max_tokens, model) -> T:
    import httpx
    base = os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1").rstrip("/")
    headers = {"Authorization": f"Bearer {os.getenv('LLM_API_KEY', 'none')}"}
    body = {"model": os.getenv("LLM_MODEL", model), "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": _flatten(system_blocks)}, {"role": "user", "content": user}],
            "response_format": {"type": "json_schema", "json_schema": {"name": schema.__name__, "schema": schema.model_json_schema()}}}
    last = None
    for _ in range(2):
        r = httpx.post(f"{base}/chat/completions", json=body, headers=headers, timeout=600)
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        try:
            return schema.model_validate_json(_extract_json(text))
        except ValidationError as e:
            last = e
            body["messages"].append({"role": "assistant", "content": text})
            body["messages"].append({"role": "user", "content": f"That JSON did not match the schema: {e}. Reply with corrected JSON only."})
    raise last


def _claude_code(system_blocks, user, schema: Type[T], effort, max_tokens, model) -> T:
    prompt = (user + "\n\nReply with one JSON object only, matching this JSON schema:\n" + json.dumps(schema.model_json_schema()))
    out = subprocess.run(["claude", "-p", prompt, "--output-format", "json", "--append-system-prompt", _flatten(system_blocks)],
                         capture_output=True, text=True, timeout=1200)
    if out.returncode != 0:
        raise RuntimeError(out.stderr[-2000:])
    result = json.loads(out.stdout).get("result", "")
    return schema.model_validate_json(_extract_json(result))


def structured(system_blocks: list[dict], user: str, schema: Type[T], effort: str = "medium",
               max_tokens: int = 8000, model: str | None = None) -> T:
    from . import config  # loads .env
    model = model or config.MODEL_TAILOR
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    fn = {"anthropic": _anthropic, "openai_compat": _openai_compat, "claude_code": _claude_code}[provider]
    return fn(system_blocks, user, schema, effort, max_tokens, model)
