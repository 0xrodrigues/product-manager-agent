import json
import re
from typing import List, Optional, cast

from openai import OpenAI
from openai import OpenAIError
from openai.types.chat import ChatCompletionMessageParam

from app.agents.parsing import extract_json_str
from app.models.story import RefinedStory

_JSON_FENCE_START = re.compile(r"```\s*json\s*", re.IGNORECASE)


class LLMError(Exception):
    pass


class LLMClient:
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        base_url = base_url.rstrip("/")
        self._model = model
        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url or None,
        )

    def complete(self, messages: List[dict], system: Optional[str] = None) -> str:
        """
        Calls the Chat Completions API via the official OpenAI Python SDK.
        If `system` is provided it is prepended as a system message.
        """
        payload_messages = list(messages)
        if system:
            payload_messages = [{"role": "system", "content": system}] + payload_messages

        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=cast(List[ChatCompletionMessageParam], payload_messages),
                timeout=60.0,
            )
        except OpenAIError as exc:
            raise LLMError(f"LLM request error: {exc}") from exc

        if not completion.choices:
            raise LLMError(f"Unexpected LLM response (no choices): {completion}")

        content = completion.choices[0].message.content
        if content is None:
            raise LLMError(f"Unexpected LLM response (empty content): {completion}")

        return content

    def extract_refined_story(self, response: str) -> Optional[RefinedStory]:
        """
        Parses a RefinedStory from the first ```json ... ``` fence in `response`.
        Falls back to scanning the raw text if no fence is found.
        Balanced-brace parsing handles nested objects and `}` inside strings.
        """
        pos = 0
        while True:
            m = _JSON_FENCE_START.search(response, pos)
            if not m:
                raw = extract_json_str(response)
                if raw is None:
                    return None
                try:
                    return RefinedStory(**json.loads(raw))
                except Exception:
                    return None
            block_start = m.end()
            close = response.find("```", block_start)
            if close < 0:
                return None
            block = response[block_start:close].strip()
            raw = extract_json_str(block)
            if raw is None:
                pos = close + 3
                continue
            try:
                return RefinedStory(**json.loads(raw))
            except Exception:
                pos = close + 3
                continue
