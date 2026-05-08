# Session Store — User Session Control

## Metadata
- Creation date: 2026-05-08
- Last update: 2026-05-08
- Document version: 1.0.0
- Main technical path: `app/services/session_store.py`

## Overview
The session store is a lightweight in-memory service that manages conversational refinement sessions. Each session holds the full message history and the most recently refined user story, allowing the AI agent to maintain context across multiple HTTP requests from the same user.

## Scope
- **Includes:** session lifecycle (create, read, update, delete), in-memory storage, data models for session and messages
- **Does not include:** persistence to disk or database, session expiration/TTL, authentication or authorization, concurrency control

## Components Involved
- `app/services/session_store.py`: CRUD operations over a module-level dict
- `app/models/session.py`: `Session`, `SessionMessage`, and `SessionResponse` Pydantic models
- `app/models/story.py`: `RefinedStory` — stored as `session.last_refined_story`
- `app/api/routes.py`: API layer that drives session lifecycle via HTTP endpoints

## Execution Flow

### Session creation (`POST /stories/session`)
1. `session_store.create_session()` generates a UUID4, instantiates a `Session`, stores it in `_store`, and returns it.
2. `ConversationAgent().start(session, raw)` runs the initial AI refinement and appends the first turn to `session.history`.
3. `session_store.update_session(session)` writes the mutated session back to `_store`.
4. API returns `SessionResponse` with `session_id`, `refined_story`, and the agent's opening `message`.
5. On failure, `session_store.delete_session(session.id)` removes the orphaned session before raising HTTP 502.

### Conversation turn (`POST /stories/session/{session_id}`)
1. `session_store.get_session(session_id)` retrieves the session; returns `None` if absent → HTTP 404.
2. `ConversationAgent().process(session, message)` appends the user message and the agent reply to `session.history` and updates `session.last_refined_story`.
3. `session_store.update_session(session)` persists the updated session back to `_store`.

### Confirmation (`POST /stories/session/{session_id}/confirm`)
1. `session_store.get_session(session_id)` retrieves session; HTTP 404 if absent.
2. HTTP 422 if `session.last_refined_story` is `None`.
3. Jira ticket is created from `session.last_refined_story`.
4. `session_store.delete_session(session_id)` removes the session — no further interaction is possible.

### Discard (`DELETE /stories/session/{session_id}`)
1. `session_store.get_session(session_id)` checks existence; HTTP 404 if absent.
2. `session_store.delete_session(session_id)` removes the session without creating a ticket.

## Data Contracts and Structures

### `Session` (Pydantic BaseModel — `app/models/session.py:14`)
| Field | Type | Default | Description |
|---|---|---|---|
| `id` | `str` | required | UUID4 string, used as store key |
| `history` | `list[SessionMessage]` | `[]` | Ordered conversation turns |
| `last_refined_story` | `RefinedStory \| None` | `None` | Latest AI-refined story |
| `created_at` | `datetime` | `datetime.now(timezone.utc)` | UTC timestamp of session creation |

### `SessionMessage` (Pydantic BaseModel — `app/models/session.py:9`)
| Field | Type | Values |
|---|---|---|
| `role` | `Literal["user", "assistant"]` | Identifies message author |
| `content` | `str` | Raw text of the turn |

### `SessionResponse` (API output — `app/models/session.py:22`)
| Field | Type | Description |
|---|---|---|
| `session_id` | `str` | The session UUID returned to the client |
| `refined_story` | `RefinedStory` | Current refined story after the turn |
| `message` | `str` | Agent's conversational reply |

### Internal store
- **Type:** `dict[str, Session]` (`_store` module-level variable)
- **Key:** `session.id` (UUID4 string)
- **Scope:** single Python process; not shared across workers or restarts

## Business Rules and Behavior
- Every session starts with a unique UUID4 id; collisions are statistically negligible.
- `get_session` returns `None` for unknown IDs — callers are responsible for raising HTTP 404.
- `update_session` is a full replace (not a merge); the caller mutates the object in place and writes it back.
- `delete_session` uses `dict.pop(key, None)` — silently no-ops if the key is absent.
- Confirming a session (`/confirm`) deletes it immediately after ticket creation; the session cannot be reused.
- A session deleted mid-conversation (e.g. via `DELETE`) leaves no trace; subsequent requests with that ID return 404.

## Error Handling
- **Session not found:** `get_session` returns `None`; routes convert this to HTTP 404 before any agent call.
- **No story to confirm:** routes raise HTTP 422 if `session.last_refined_story is None` before touching Jira.
- **Agent failure on start:** the session is deleted before raising HTTP 502 to avoid orphaned sessions accumulating in `_store`.
- The store itself raises no exceptions — all operations are safe by design (`dict.pop` with default, `dict.get`).

## Integration with Project
- `app/api/routes.py` is the sole consumer of `session_store`; it drives the full lifecycle.
- `app/agents/conversation_agent.py` receives the `Session` object directly and mutates `history` and `last_refined_story` in place.
- `app/integrations/jira.py` is called at confirmation time using data read from `session.last_refined_story`.

## Current Limitations
- **No persistence:** all sessions are lost when the server process restarts or crashes.
- **Single-process only:** not safe for multi-worker deployments (e.g. `uvicorn --workers N` or gunicorn); each worker maintains an independent `_store`.
- **No TTL or expiration:** abandoned sessions accumulate indefinitely for the lifetime of the process.
- **No concurrency protection:** concurrent requests for the same session ID are not serialized; race conditions are possible under load.
- **No session listing or inspection endpoint:** there is no admin API to enumerate or inspect active sessions.

## Recommended Evolution Points
- Replace `_store` dict with a Redis-backed store to support persistence, multi-worker deployments, and built-in key TTL for automatic cleanup.
- Add a session TTL (e.g. 30 minutes of inactivity) enforced either at the store level or via Redis expiry.
- Introduce an async-safe lock (e.g. `asyncio.Lock` per session ID) if the API is migrated to async FastAPI handlers.
- Add a `GET /stories/session/{session_id}` endpoint to allow clients to recover session state after a disconnect.

## References
- Source code: `app/services/session_store.py`
- Session models: `app/models/session.py`
- Story models: `app/models/story.py`
- API routes: `app/api/routes.py`
