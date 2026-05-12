# Session Store — Controle de Sessões de Usuário

## Metadados
- Data de criação: 2026-05-08
- Última atualização: 2026-05-08
- Versão do documento: 1.0.0
- Caminho técnico principal: `app/services/session_store.py`

## Visão Geral
O session store é um serviço leve em memória que gerencia sessões de refinamento conversacional. Cada sessão mantém o histórico completo de mensagens e a história refinada mais recente, permitindo que o agente de IA preserve contexto entre múltiplas requisições HTTP do mesmo usuário.

## Escopo
- **Inclui:** ciclo de vida da sessão (criar, ler, atualizar, deletar), armazenamento em memória, modelos de dados para sessão e mensagens.
- **Não inclui:** persistência em disco ou banco de dados, expiração/TTL de sessão, autenticação ou autorização, controle de concorrência.

## Componentes Envolvidos
- `app/services/session_store.py`: operações CRUD sobre um dicionário de nível de módulo.
- `app/models/session.py`: modelos Pydantic `Session`, `SessionMessage` e `SessionResponse`.
- `app/models/story.py`: `RefinedStory` — armazenado como `session.last_refined_story`.
- `app/api/routes.py`: camada de API que conduz o ciclo de vida da sessão via endpoints HTTP.

## Fluxo de Execução

### Criação de sessão — `POST /stories/session`
1. `session_store.create_session()` gera um UUID4, instancia uma `Session`, armazena em `_store` e a retorna.
2. `ConversationAgent().start(session, raw)` executa o refinamento inicial pela IA e acrescenta o primeiro turno em `session.history`.
3. `session_store.update_session(session)` escreve a sessão mutada de volta em `_store`.
4. A API retorna `SessionResponse` com `session_id`, `refined_story` e a `message` de abertura do agente.
5. Em caso de falha, `session_store.delete_session(session.id)` remove a sessão órfã antes de lançar HTTP 502.

### Turno de conversa — `POST /stories/session/{session_id}`
1. `session_store.get_session(session_id)` recupera a sessão; retorna `None` se ausente → HTTP 404.
2. `ConversationAgent().process(session, message)` acrescenta a mensagem do usuário e a resposta do agente em `session.history` e atualiza `session.last_refined_story`.
3. `session_store.update_session(session)` persiste a sessão atualizada de volta em `_store`.

### Confirmação — `POST /stories/session/{session_id}/confirm`
1. `session_store.get_session(session_id)` recupera a sessão; HTTP 404 se ausente.
2. HTTP 422 se `session.last_refined_story` for `None`.
3. O ticket Jira é criado a partir de `session.last_refined_story`.
4. `session_store.delete_session(session_id)` remove a sessão — nenhuma interação posterior é possível.

### Descarte — `DELETE /stories/session/{session_id}`
1. `session_store.get_session(session_id)` verifica existência; HTTP 404 se ausente.
2. `session_store.delete_session(session_id)` remove a sessão sem criar ticket.

## Contratos de Dados e Estruturas

### `Session` (Pydantic BaseModel — `app/models/session.py`)
| Campo | Tipo | Padrão | Descrição |
|---|---|---|---|
| `id` | `str` | obrigatório | String UUID4, usada como chave no store |
| `history` | `list[SessionMessage]` | `[]` | Turnos de conversa em ordem |
| `last_refined_story` | `RefinedStory \| None` | `None` | Última história refinada pela IA |
| `created_at` | `datetime` | `datetime.now(timezone.utc)` | Timestamp UTC de criação da sessão |

### `SessionMessage` (Pydantic BaseModel — `app/models/session.py`)
| Campo | Tipo | Valores |
|---|---|---|
| `role` | `Literal["user", "assistant"]` | Identifica o autor da mensagem |
| `content` | `str` | Texto bruto do turno |

### `SessionResponse` (saída da API — `app/models/session.py`)
| Campo | Tipo | Descrição |
|---|---|---|
| `session_id` | `str` | UUID da sessão retornado ao cliente |
| `refined_story` | `RefinedStory` | História refinada atual após o turno |
| `message` | `str` | Resposta conversacional do agente |

### Store interno
- **Tipo:** `dict[str, Session]` (variável de nível de módulo `_store`)
- **Chave:** `session.id` (string UUID4)
- **Escopo:** processo Python único; não compartilhado entre workers ou reinicializações

## Regras de Negócio e Comportamento
- Cada sessão inicia com um UUID4 único; colisões são estatisticamente negligenciáveis.
- `get_session` retorna `None` para IDs desconhecidos — os chamadores são responsáveis por lançar HTTP 404.
- `update_session` é uma substituição completa (não merge); o chamador muta o objeto in-place e o escreve de volta.
- `delete_session` usa `dict.pop(key, None)` — opera silenciosamente se a chave estiver ausente.
- Confirmar uma sessão (`/confirm`) a deleta imediatamente após a criação do ticket; a sessão não pode ser reutilizada.
- Uma sessão deletada durante a conversa (ex.: via `DELETE`) não deixa rastro; requisições subsequentes com esse ID retornam 404.

## Tratamento de Erros
- **Sessão não encontrada:** `get_session` retorna `None`; as rotas convertem para HTTP 404 antes de qualquer chamada ao agente.
- **Sem história para confirmar:** as rotas lançam HTTP 422 se `session.last_refined_story is None` antes de acessar o Jira.
- **Falha do agente na inicialização:** a sessão é deletada antes de lançar HTTP 502 para evitar acúmulo de sessões órfãs em `_store`.
- O store em si não lança exceções — todas as operações são seguras por design (`dict.pop` com default, `dict.get`).

## Integração com o Projeto
- `app/api/routes.py` é o único consumidor do `session_store`; conduz o ciclo de vida completo.
- `app/agents/conversation_agent.py` recebe o objeto `Session` diretamente e muta `history` e `last_refined_story` in-place.
- `app/integrations/jira.py` é chamado no momento da confirmação com dados lidos de `session.last_refined_story`.

## Limitações Atuais
- **Sem persistência:** todas as sessões são perdidas quando o processo do servidor reinicia ou cai.
- **Apenas processo único:** não é seguro para deployments multi-worker (ex.: `uvicorn --workers N` ou gunicorn); cada worker mantém um `_store` independente.
- **Sem TTL ou expiração:** sessões abandonadas acumulam indefinidamente durante a vida do processo.
- **Sem proteção de concorrência:** requisições concorrentes para o mesmo `session_id` não são serializadas; race conditions são possíveis sob carga.
- **Sem endpoint de listagem ou inspeção:** não existe API administrativa para enumerar ou inspecionar sessões ativas.

## Pontos de Evolução Recomendados
- Substituir o dicionário `_store` por um store com Redis para suportar persistência, deployments multi-worker e TTL nativo para limpeza automática.
- Adicionar TTL de sessão (ex.: 30 minutos de inatividade) aplicado no nível do store ou via expiração do Redis.
- Introduzir lock async-safe (ex.: `asyncio.Lock` por `session_id`) caso a API seja migrada para handlers assíncronos do FastAPI.
- Adicionar endpoint `GET /stories/session/{session_id}` para permitir que clientes recuperem o estado da sessão após uma desconexão.

## Referências
- Código-fonte: `app/services/session_store.py`
- Modelos de sessão: `app/models/session.py`
- Modelos de história: `app/models/story.py`
- Rotas da API: `app/api/routes.py`
