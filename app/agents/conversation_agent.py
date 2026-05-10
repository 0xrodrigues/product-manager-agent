import logging
from pathlib import Path

from app.agents.llm_client import LLMClient, LLMError
from app.agents.parsing import parse_json_object
from app.config import settings
from app.models.session import Session, SessionMessage
from app.models.story import RawStory, RefinedStory

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "conversation_system.txt"
_REFINE_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "refine_story.txt"


def _build_initial_user_message(raw: RawStory) -> str:
    template = _REFINE_PROMPT_PATH.read_text(encoding="utf-8")
    return template.format(title=raw.title, description=raw.description)


def _parse_conversation_response(response: str) -> tuple[RefinedStory, str]:
    raw_json = parse_json_object(response)
    story = RefinedStory(**raw_json["refined_story"])
    message = raw_json.get("message", "")
    return story, message


class ConversationAgent:
    """Maintains multi-turn refinement of a user story within a session."""

    def __init__(self) -> None:
        self._llm = LLMClient(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )
        self._system_prompt = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")

    def process(self, session: Session, user_message: str) -> tuple[RefinedStory, str]:
        """Send the full conversation history plus the new user message to the LLM.

        Updates session.history in place and returns the refined story and agent message.

        Raises:
            ValueError: on API failures or invalid model output.
        """
        session.history.append(SessionMessage(role="user", content=user_message))

        messages = [{"role": m.role, "content": m.content} for m in session.history]
        logger.info("Processing conversation turn for session %s", session.id)

        try:
            response = self._llm.complete(messages=messages, system=self._system_prompt)
        except LLMError as exc:
            logger.error("LLM call failed for session %s: %s", session.id, exc)
            raise ValueError(str(exc)) from exc

        try:
            story, message = _parse_conversation_response(response)
        except (ValueError, KeyError, TypeError) as exc:
            logger.error("Failed to parse model response for session %s: %s", session.id, response)
            raise ValueError(f"Model returned invalid output: {exc}") from exc

        session.history.append(SessionMessage(role="assistant", content=response))
        session.last_refined_story = story
        return story, message

    def start(self, session: Session, raw: RawStory) -> tuple[RefinedStory, str]:
        """Bootstrap a new session with the initial raw story."""
        initial_message = _build_initial_user_message(raw)
        return self.process(session, initial_message)
