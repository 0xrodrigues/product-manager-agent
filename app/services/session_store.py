import uuid

from app.models.session import Session

_store: dict[str, Session] = {}


def create_session() -> Session:
    session = Session(id=str(uuid.uuid4()))
    _store[session.id] = session
    return session


def get_session(session_id: str) -> Session | None:
    return _store.get(session_id)


def update_session(session: Session) -> None:
    _store[session.id] = session


def delete_session(session_id: str) -> None:
    _store.pop(session_id, None)
