# Modo Entrevistador — PM Agent

## O que é

Antes de gerar a história, o agente conduz uma entrevista com o PM para entender profundamente a demanda. As 3 perguntas iniciais são o ponto de partida — após isso, o agente decide livremente se precisa de mais informações ou se já tem contexto suficiente para gerar a história.

A cada pergunta, o agente oferece uma sugestão de resposta para ancorar o PM e reduzir esforço cognitivo.

---

## Fluxo

```
PM envia o tema inicial
        ↓
Agente faz as 3 perguntas base (uma por vez, com sugestão)
        ↓
PM responde cada pergunta
        ↓
Agente avalia se tem contexto suficiente
        ├── Não tem → faz mais perguntas (com sugestão) até ter
        └── Tem     → gera a história completa
                            ↓
                   Conversa livre para refinamento
```

---

## Estados da sessão

Adicionar o campo `phase` no modelo `Session`:

```
interviewing  → agente ainda está coletando informações
refining      → história já foi gerada, PM está refinando
```

A transição de `interviewing` para `refining` é feita pelo próprio agente quando ele decidir que tem contexto suficiente para gerar a história. Não há número fixo de perguntas além das 3 iniciais.

---

## Parte 1 — Modelo de sessão

Em `app/models/session.py`, adicionar o campo `phase` no modelo `Session`:

```python
from enum import Enum

class SessionPhase(str, Enum):
    INTERVIEWING = "interviewing"
    REFINING = "refining"
```

Adicionar `phase: SessionPhase = SessionPhase.INTERVIEWING` no modelo `Session`.

A transição para `REFINING` deve ocorrer quando o agente retornar `refined_story` preenchido pela primeira vez.

---

## Parte 2 — Dois prompts de sistema

### `prompts/interview_system.txt`

```
You are a senior Product Manager conducting a structured interview to deeply understand a feature demand before writing a user story.

Your goal is to gather enough context to generate a complete, accurate, and unambiguous user story.

Start by asking the following 3 questions, one at a time. After each question, provide a short suggestion to guide the PM's answer.

Question 1: What is the business problem or need this feature addresses?
Question 2: Who is the main actor and what is the expected flow — what happens before, during, and after?
Question 3: What constraints, business rules, or technical dependencies do you already know about?

After the 3 initial questions, evaluate whether you have enough context. If not, continue asking targeted questions — always one at a time, always with a suggestion.

When you are confident you have sufficient context, generate the complete user story.

Response format during interview (phase: interviewing):
Return a JSON object with:
- "phase": "interviewing"
- "question": the next question to ask the PM
- "suggestion": a short example answer to guide the PM (2-3 sentences max)
- "refined_story": null

Response format when ready to generate (phase: refining):
Return a JSON object with:
- "phase": "refining"
- "question": null
- "suggestion": null
- "refined_story": the complete story object (same schema as always)
- "message": short message explaining the story or asking for refinement

The "refined_story" must always contain:
- "title": clear and descriptive
- "user_story": written in the same language as the user, following the structure: "<role> wants <goal> so that <reason>"
- "functional_requirements": list of strings
- "business_rules": list of strings
- "acceptance_criteria": list of strings in Gherkin format — translate keywords to the user's language (e.g. Portuguese: "Dado/Quando/Então")
- "dependencies": list of technical system dependencies (APIs, services, tables, contract fields required from other teams) — empty list if none
- "story_points": Fibonacci number or null

Before generating the story, validate it against the Definition of Ready:
1. Title is clear and descriptive
2. User story follows the correct structure
3. Functional requirements are listed and understandable
4. Business rules are identified
5. Acceptance criteria are in Gherkin format
6. Dependencies are identified or explicitly stated as none
7. Story points are estimated

If any item cannot be filled with confidence, ask the PM before generating.

IMPORTANT: Return only the raw JSON object. No markdown, no backticks, no explanation outside the JSON.
Always respond in the same language as the user.
Never mix languages within a single response. All text must be in the user's language only.
```

---

### `prompts/conversation_system.txt`

Manter o prompt atual sem alterações. Ele continua sendo usado na fase `refining`.

---

## Parte 3 — Agente de entrevista

Criar `app/agents/interview_agent.py`:

- Carrega `prompts/interview_system.txt` como system prompt
- Recebe a sessão atual e a nova mensagem do PM
- Monta o histórico completo e envia para a LLM
- Faz parse do JSON retornado
- Retorna o objeto com `phase`, `question`, `suggestion` e `refined_story`
- Atualiza o histórico da sessão

---

## Parte 4 — Orquestração no endpoint de mensagem

Em `app/api/routes.py`, no endpoint `POST /stories/session/{session_id}`, alterar a lógica para:

```
if session.phase == INTERVIEWING:
    chamar interview_agent
    if response.phase == "refining":
        atualizar session.phase para REFINING
        salvar refined_story em session.last_refined_story
else:
    chamar conversation_agent
```

O endpoint `POST /stories/session` (criação) também deve chamar o `interview_agent` com o input inicial do PM, iniciando já com a primeira pergunta.

---

## Parte 5 — Resposta da API

Atualizar `app/models/session.py` para o `SessionResponse` incluir os novos campos:

```python
class SessionResponse(BaseModel):
    session_id: str
    phase: SessionPhase
    question: str | None = None
    suggestion: str | None = None
    refined_story: RefinedStory | None = None
    message: str | None = None
```

---

## Parte 6 — Frontend

Em `frontend/js/app.js`, adaptar o rendering da resposta do agente:

- Se `phase == "interviewing"`: renderizar apenas a pergunta e a sugestão em formato de chat — sem story card
- Se `phase == "refining"`: renderizar o story card completo como hoje

A sugestão deve aparecer como texto secundário abaixo da pergunta, visualmente diferenciado (cor mais suave, fonte menor).

---

## O que não muda

- `app/integrations/jira.py`
- `app/models/story.py`
- Endpoint `/confirm`
- Endpoint `DELETE`
- Prompt `conversation_system.txt`