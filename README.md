# Product Manager Agent

Um agente de IA que ajuda PMs a refinarem e criarem histórias de usuário no Jira. O PM descreve uma funcionalidade em texto livre — pode ser uma frase, um parágrafo ou uma transcrição de reunião — e o agente conduz uma entrevista estruturada, refina a história e cria o ticket no Jira automaticamente.

---

## Problema

PMs perdem tempo transformando ideias brutas em tickets bem escritos. Escrever descrição, requisitos funcionais, regras de negócio e critérios de aceite é repetitivo e frequentemente inconsistente entre histórias.

---

## Solução

O PM escreve o que quer e o agente:

1. Conduz uma entrevista para coletar informações faltantes
2. Gera uma história estruturada (RF / RN / CA)
3. Itera com o PM até a história estar aprovada
4. Cria o ticket no Jira automaticamente

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.11+ / FastAPI |
| LLM | OpenAI-compatible API (configurável) |
| Integração | Jira REST API v3 / Confluence REST API |
| Frontend | HTML/CSS/JS estático |

---

## Arquitetura

```
app/
├── api/
│   └── routes.py          # Rotas HTTP — orquestração pura, sem lógica de negócio
├── agents/
│   ├── interview_agent.py  # Fase de entrevista: faz perguntas ao PM
│   └── conversation_agent.py  # Fase de refinamento: itera sobre a história
├── core/
│   ├── llm.py             # Cliente OpenAI-compatible
│   ├── parsing.py         # Extração de JSON da resposta do LLM
│   └── formatting.py      # Numeração RF/RN/CA e montagem do texto
├── models/
│   ├── story.py           # RawStory, RefinedStory, JiraTicket, ...
│   └── session.py         # Session, SessionPhase, SessionResponse
├── services/
│   ├── jira.py            # Cliente Jira
│   ├── confluence.py      # Cliente Confluence
│   └── session_store.py   # Sessões em memória
└── prompts/               # Templates de prompt (.txt)
```

### Fluxo de sessão

```
POST /api/stories/session          →  Cria sessão, inicia entrevista
POST /api/stories/session/{id}     →  Resposta do PM → próxima pergunta ou refinamento
POST /api/stories/session/{id}/confirm  →  Aprova história e cria ticket no Jira
DELETE /api/stories/session/{id}   →  Descarta sessão sem criar ticket
```

### Fases da sessão

```
INTERVIEWING  →  InterviewAgent faz perguntas para coletar requisitos
      ↓  (agente sinaliza phase=refining)
REFINING      →  ConversationAgent itera a história com o PM
      ↓  (PM confirma)
CONFIRMED     →  Ticket criado no Jira, sessão encerrada
```

---

## Estrutura de uma história gerada

Cada história é composta por:

- **Título** — sumário da história
- **User Story** — "Como [persona], quero [ação] para [benefício]"
- **Requisitos Funcionais (RF-01, RF-02…)** — o que o sistema deve fazer
- **Regras de Negócio (RN-01, RN-02…)** — restrições e políticas
- **Critérios de Aceite (CA-01, CA-02…)** — condições de conclusão
- **Dependências** — outros tickets ou sistemas
- **Story Points** — estimativa de esforço

---

## Configuração

### 1. Clonar e instalar dependências

```bash
git clone <repo-url>
cd product-manager-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Variáveis de ambiente

Copie o arquivo de exemplo e preencha os valores:

```bash
cp .env.example .env
```

```env
# LLM (qualquer API OpenAI-compatible)
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_api_key_here
LLM_MODEL=gpt-4o

# Atlassian
ATLASSIAN_BASE_URL=https://your-org.atlassian.net
ATLASSIAN_USER_EMAIL=you@example.com
ATLASSIAN_API_TOKEN=your_atlassian_api_token_here
ATLASSIAN_SSL_VERIFY=true

# Jira (desabilitado por padrão — retorna ticket mock)
JIRA_ENABLED=false
JIRA_PROJECT_KEY=PROJ

# Confluence (desabilitado por padrão)
CONFLUENCE_ENABLED=false
```

### 3. Rodar o servidor

```bash
uvicorn app.main:app --reload
```

O frontend estático estará disponível em `http://localhost:8000`.  
A documentação interativa da API estará em `http://localhost:8000/docs`.

---

## Uso via API

### Iniciar uma sessão

```bash
curl -X POST http://localhost:8000/api/stories/session \
  -H "Content-Type: application/json" \
  -d '{"title": "Notificação de pagamento", "description": "O usuário precisa receber um aviso quando o pagamento for aprovado"}'
```

Resposta:
```json
{
  "session_id": "abc-123",
  "phase": "interviewing",
  "question": "Quais canais de notificação devem ser suportados (e-mail, push, SMS)?",
  "suggestion": null,
  "refined_story": null,
  "message": null
}
```

### Responder à entrevista

```bash
curl -X POST http://localhost:8000/api/stories/session/abc-123 \
  -H "Content-Type: application/json" \
  -d '{"message": "E-mail e push notification"}'
```

### Confirmar e criar ticket no Jira

```bash
curl -X POST http://localhost:8000/api/stories/session/abc-123/confirm
```

### Descartar sessão

```bash
curl -X DELETE http://localhost:8000/api/stories/session/abc-123
```

---

## Testes

```bash
pytest
```

Os testes espelham a estrutura de `app/`:

```
tests/
├── test_agents/
├── test_api/
└── test_integrations/
```

---

## Notas de implementação

- **Sessões em memória**: o `session_store` não persiste dados. Reiniciar o servidor encerra todas as sessões ativas. Para múltiplas instâncias, substituir por Redis ou banco relacional.
- **Jira desabilitado por padrão**: com `JIRA_ENABLED=false`, o endpoint de confirmação retorna um ticket mock (`MOCK-0`) sem chamar a API do Jira. Útil para desenvolvimento e testes.
- **LLM plugável**: o cliente em `app/core/llm.py` aceita qualquer API compatível com OpenAI (Anthropic via proxy, Ollama, Azure OpenAI, etc.) — basta ajustar `LLM_BASE_URL` e `LLM_MODEL`.
