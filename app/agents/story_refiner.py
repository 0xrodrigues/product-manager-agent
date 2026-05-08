import logging
from pathlib import Path

from app.config import settings
from app.models.story import RawStory, RefinedStory
from app.agents.llm_client import LLMClient, LLMError

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "refine_story.txt"


class StoryRefinerAgent:
    """Uses Claude to transform a raw story description into a structured user story."""

    def __init__(self) -> None:
        self._llm = LLMClient(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )
        self._prompt_template = _PROMPT_PATH.read_text(encoding="utf-8")

    def refine(self, raw: RawStory) -> RefinedStory:
        """Send the raw story to Claude and return the refined result.

        Raises:
            ValueError: on API failures or invalid model output.
        """
        prompt = self._prompt_template.format(
            title=raw.title,
            description=raw.description,
        )
        logger.info("Refining story: %s", raw.title)

        try:
            response = self._llm.complete(messages=[{"role": "user", "content": prompt}])
        except LLMError as exc:
            logger.error("LLM call failed: %s", exc)
            raise ValueError(str(exc)) from exc

        refined = self._llm.extract_refined_story(response)
        if refined is None:
            logger.error("Model returned unparseable output: %s", response)
            raise ValueError("Model did not return valid JSON")

        return refined
