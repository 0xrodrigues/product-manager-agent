import logging
from pathlib import Path

from pydantic import BaseModel

from app.core.llm import LLMClient, LLMError
from app.core.parsing import parse_json_object
from app.config import settings
from app.models.session import Session, SessionMessage
from app.models.story import RawStory, RefinedStory

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "interview_system.txt"


class InterviewResponse(BaseModel):
    phase: str
    question: str | None = None
    suggestion: str | None = None
    refined_story: RefinedStory | None = None
    message: str | None = None


def _parse_interview_response(response: str) -> InterviewResponse:
    raw_json = parse_json_object(response)
    refined_story = None
    if raw_json.get("refined_story"):
        refined_story = RefinedStory(**raw_json["refined_story"])

    return InterviewResponse(
        phase=raw_json["phase"],
        question=raw_json.get("question"),
        suggestion=raw_json.get("suggestion"),
        refined_story=refined_story,
        message=raw_json.get("message"),
    )


class InterviewAgent:
    """Conducts a structured interview with the PM before generating a user story."""

    def __init__(self) -> None:
        self._llm = LLMClient(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )
        self._system_prompt = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")

    def process(self, session: Session, user_message: str) -> InterviewResponse:
        """Send the full conversation history plus the new user message to the LLM.

        Updates session.history in place and returns the interview response.

        Raises:
            ValueError: on API failures or invalid model output.
        """
        session.history.append(SessionMessage(role="user", content=user_message))

        messages = [{"role": m.role, "content": m.content} for m in session.history]
        logger.info("Processing interview turn for session %s", session.id)

        try:
            response = self._llm.complete(messages=messages, system=self._system_prompt)
        except LLMError as exc:
            logger.error("LLM call failed for session %s: %s", session.id, exc)
            raise ValueError(str(exc)) from exc

        try:
            result = _parse_interview_response(response)
        except (ValueError, KeyError, TypeError) as exc:
            logger.error("Failed to parse interview response for session %s: %s", session.id, response)
            raise ValueError(f"Model returned invalid output: {exc}") from exc

        session.history.append(SessionMessage(role="assistant", content=response))
        if result.refined_story:
            session.last_refined_story = result.refined_story

        return result

    def start(self, session: Session, raw: RawStory) -> InterviewResponse:
        """Bootstrap a new interview session with the initial raw story."""
        initial_message = f"{raw.title}\n\n{raw.description}" if raw.description != raw.title else raw.title
        return self.process(session, initial_message)
