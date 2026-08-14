import json
import re

from langchain_openai import ChatOpenAI

from app.config import settings

# DeepSeek exposes an OpenAI-compatible API, so we just point ChatOpenAI at
# their base URL instead of using a DeepSeek-specific client.
llm = ChatOpenAI(
    model=settings.deepseek_model_id,
    api_key=settings.deepseek_api_key,
    base_url="https://api.deepseek.com",
    temperature=0.4,
    max_tokens=1024,
)


def parse_llm_json(text: str) -> dict:
    """Parses a model response that's supposed to be raw JSON, tolerating the
    common ways models deviate from "respond ONLY with JSON" (hit in testing
    with DeepSeek): wrapping the response in ```json ... ``` fences, or adding
    stray text before/after the JSON object. Used by every agent that asks the
    LLM for structured output, so this failure mode gets fixed everywhere at
    once instead of per-agent.
    """
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Last resort: pull out the first {...} block in case there's stray
        # prose around the JSON despite the prompt's instructions.
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise
