# Conversational Story Refinement

## O que é

Evolução do agente para suportar múltiplos turnos de conversa. Em vez de gerar a história em uma única chamada, o PM pode iterar com o agente até estar satisfeito e só então criar o ticket no Jira.

---

## Conceitos novos

**Sessão:** cada refinamento vira uma sessão identificada por um ID único. A sessão armazena o histórico completo da conversa enquanto estiver ativa.

**Histórico:** a cada mensagem nova, todo o histórico da sessão é enviado para a LLM. É assim que o modelo mantém contexto entre os turnos.

**Estado em memória:** no piloto, as sessões ficam armazenadas em memória no próprio processo. Reiniciando o servidor as sessões somem — aceitável para agora. Em produção, migrar para Redis.

---

## Novos endpoints

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/stories/session` | Cria sessão e retorna refinamento inicial |
| POST | `/stories/session/{id}` | Envia mensagem e recebe resposta refinada |
| POST | `/stories/session/{id}/confirm` | PM aprova e cria ticket no Jira |
| DELETE | `/stories/session/{id}` | Descarta sessão sem criar ticket |

---

## Parte 1 — Modelo de sessão

Criar `app/models/session.py` com os seguintes modelos:

- `SessionMessage` — representa uma mensagem no histórico com campos `role` (`user` ou `assistant`) e `content`
- `Session` — representa a sessão completa com campos `id`, `history` (lista de `SessionMessage`), `last_refined_story` (último `RefinedStory` gerado), `created_at`
- `SessionResponse` — resposta retornada ao PM com campos `session_id`, `refined_story`, `message` (comentário textual do agente sobre o refinamento)

---

## Parte 2 — Gerenciamento de sessões

Criar `app/services/session_store.py`:

- Dicionário em memória como store `dict[str, Session]`
- Função `create_session() -> Session` — gera UUID, instancia sessão vazia, armazena e retorna
- Função `get_session(session_id: str) -> Session | None` — retorna sessão ou None
- Função `update_session(session: Session) -> None` — persiste estado atualizado
- Função `delete_session(session_id: str) -> None` — remove sessão do store

---

## Parte 3 — Agente conversacional

Criar `app/agents/conversation_agent.py`:

- Recebe a sessão atual e a nova mensagem do PM
- Monta o histórico completo para enviar à LLM
- Usa um system prompt separado (`prompts/conversation_system.txt`) que instrui o modelo a atuar como um PM sênior refinando histórias iterativamente
- A cada turno, retorna um `RefinedStory` atualizado e uma mensagem textual explicando o que mudou ou perguntando o que ainda precisa ser ajustado
- Atualiza o histórico da sessão com a nova troca

**Prompt `prompts/conversation_system.txt`:**

```
You are a senior Product Manager helping refine user stories iteratively.

You will receive a conversation history and must:
1. Understand the current state of the story being refined
2. Incorporate the PM's latest feedback or question
3. Return a JSON object with two fields:
   - "refined_story": the updated story object (same schema as before)
   - "message": a short message explaining what changed or asking a clarifying question if needed

The "refined_story" must always contain:
- "title"
- "user_story": "As a <role>, I want <goal>, so that <reason>"
- "functional_requirements": list of strings
- "business_rules": list of strings
- "acceptance_criteria": list of strings in Gherkin format (Given/When/Then)
- "story_points": Fibonacci number or null

IMPORTANT: Return only the raw JSON object. No markdown, no backticks, no explanation outside the JSON.
Always respond in the same language as the user.
```

---

## Parte 4 — Endpoints

Atualizar `app/api/routes.py` adicionando os quatro endpoints descritos acima.

- `POST /stories/session` — recebe `RawStory`, cria sessão, chama `conversation_agent` com o input inicial, retorna `SessionResponse`
- `POST /stories/session/{session_id}` — recebe `{"message": "..."}`, recupera sessão, chama `conversation_agent`, retorna `SessionResponse`
- `POST /stories/session/{session_id}/confirm` — recupera sessão, pega `last_refined_story`, cria ticket no Jira, deleta sessão, retorna `RefineAndCreateResponse`
- `DELETE /stories/session/{session_id}` — deleta sessão, retorna 204

Tratar 404 quando sessão não existir em todos os endpoints que recebem `session_id`.

---

## O que não muda

- `app/agents/story_refiner.py` e o endpoint `/stories/refine-and-create` continuam funcionando como estão
- `app/integrations/jira.py` não muda
- `app/models/story.py` não muda