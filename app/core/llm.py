from typing import List, cast

from openai import OpenAI
from openai import OpenAIError
from openai.types.chat import ChatCompletionMessageParam


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

    def complete(self, messages: List[dict], system: str | None = None, temperature: float = 0.1) -> str:
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
                temperature=temperature,
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
