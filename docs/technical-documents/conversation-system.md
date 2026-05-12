# Sistema de Conversação

## Metadados
- Data de criação: 2026-05-08
- Última atualização: 2026-05-08
- Versão do documento: 1.0.0
- Caminho técnico principal: `app/agents/conversation_agent.py`

## Visão Geral
O sistema de conversação permite o refinamento iterativo e multi-turno de histórias de usuário por meio de uma interface estilo chat. Um Product Manager submete uma história bruta e continua trocando mensagens com a IA até que a história atenda à Definição de Pronto, e então confirma para criar um ticket no Jira.

## Escopo
- **Inclui:** ciclo de vida da sessão, interação multi-turno com LLM, parsing da história a partir da saída do modelo, validação da Definição de Pronto pelo modelo.
- **Não inclui:** lógica de criação de ticket Jira (tratada pelo `JiraClient`), refinamento avulso (não conversacional) via `/stories/refine`.

## Componentes Envolvidos
- `app/prompts/conversation_system.txt`: system prompt carregado uma vez na inicialização do agente; define a persona do modelo, o contrato de saída e o checklist da Definição de Pronto.
- `app/agents/conversation_agent.py` — `ConversationAgent`: orquestra o estado da sessão, a montagem do histórico, as chamadas ao LLM e o parsing da resposta.
- `app/agents/llm_client.py` — `LLMClient`: wrapper fino sobre o SDK OpenAI; envia o array `messages` com system prompt opcional; trata timeouts e erros do SDK.
- `app/services/session_store`: store em memória; mantém objetos `Session` indexados por UUID.
- `app/models/session.py` — `Session`, `SessionMessage`, `SessionResponse`: modelos de dados para histórico de conversa e respostas da API.
- `app/models/story.py` — `RefinedStory`: modelo Pydantic validado contra cada resposta do modelo.
- `app/api/routes.py`: rotas FastAPI que expõem os endpoints de sessão e conectam requisições HTTP ao `ConversationAgent`.

## Fluxo de Execução

### Iniciar uma sessão — `POST /stories/session`
1. A rota recebe `RawStory` (`title`, `description`).
2. `session_store.create_session()` aloca uma nova `Session` com UUID e histórico vazio.
3. `ConversationAgent.start()` formata a história bruta usando `app/prompts/refine_story.txt` e chama `ConversationAgent.process()`.
4. `process()` acrescenta a mensagem do usuário em `session.history`, monta o array completo de mensagens e o envia para `LLMClient.complete()` com o system prompt carregado de `conversation_system.txt`.
5. O modelo retorna um objeto JSON bruto; `_parse_conversation_response()` extrai `refined_story` e `message` via parsing de chaves balanceadas.
6. A resposta do assistente é acrescentada em `session.history` e `session.last_refined_story` é atualizado.
7. `session_store.update_session(session)` persiste o estado atualizado.
8. A rota retorna `SessionResponse` (`session_id`, `refined_story`, `message`).

### Continuar uma sessão — `POST /stories/session/{session_id}`
1. A rota busca a sessão pelo ID; retorna 404 se ausente.
2. `ConversationAgent.process()` é chamado com a nova mensagem do usuário.
3. O histórico completo acumulado (todos os turnos anteriores + nova mensagem) é enviado ao LLM — sem sumarização.
4. História e mensagem parseadas são retornadas; o estado da sessão é atualizado.

### Confirmar uma sessão — `POST /stories/session/{session_id}/confirm`
1. A rota recupera `session.last_refined_story`; retorna 422 se ausente.
2. Monta a descrição do Jira a partir de `user_story`, `functional_requirements`, `business_rules` e `acceptance_criteria`.
3. Cria um `JiraTicket` e chama `JiraClient.create_ticket()` (ou retorna um mock se `settings.jira_enabled` for falso).
4. A sessão é deletada do store.
5. Retorna `RefineAndCreateResponse`.

### Descartar uma sessão — `DELETE /stories/session/{session_id}`
1. Valida que a sessão existe; retorna 404 caso contrário.
2. Remove a sessão do store em memória. Nenhum ticket Jira é criado.

## Contratos de Dados e Estruturas

### Entrada
- `RawStory`: `title: str`, `description: str`
- Turnos de continuação: `{ "message": str }`

### Contrato de Saída do LLM (aplicado pelo system prompt)
O modelo deve retornar um objeto JSON bruto (sem fences markdown) com exatamente duas chaves:
```json
{
  "refined_story": {
    "title": "string",
    "user_story": "string",
    "functional_requirements": ["string"],
    "business_rules": ["string"],
    "acceptance_criteria": ["string — formato Gherkin no idioma do usuário"],
    "dependencies": ["string — ou lista vazia"],
    "story_points": "número Fibonacci ou null"
  },
  "message": "string"
}
```

### Saída
- `SessionResponse`: `session_id: str`, `refined_story: RefinedStory`, `message: str`
- `RefineAndCreateResponse` (na confirmação): `refined_story: RefinedStory`, `jira_ticket: JiraTicketResponse`

### Estado Persistido (`Session`)
- `id: str` — UUID
- `history: list[SessionMessage]` — todos os turnos `user` e `assistant` em ordem
- `last_refined_story: RefinedStory | None` — última história parseada, sobrescrita a cada turno

## Regras de Negócio e Comportamento
- O system prompt instrui o modelo a responder no mesmo idioma do usuário e nunca misturar idiomas.
- Os critérios de aceite devem seguir o formato Gherkin com palavras-chave traduzidas para o idioma do usuário.
- `dependencies` é um campo obrigatório; o modelo deve retornar uma lista vazia `[]` se não houver dependências técnicas.
- `story_points` deve ser um número Fibonacci ou `null` se ainda não estimado.
- Antes de confirmar uma história como pronta, o modelo valida os 7 itens da Definição de Pronto e faz perguntas de esclarecimento via `message` para os que estiverem faltando.
- O histórico completo da conversa é enviado a cada turno — sem janelamento ou sumarização.

## Tratamento de Erros
- `LLMError` (de `LLMClient.complete()`): logado, relançado como `ValueError`, exposto como HTTP 502.
- JSON inválido ou não parseável do modelo: `_parse_conversation_response()` lança `ValueError`; logado com a resposta bruta, exposto como HTTP 502.
- Sessão não encontrada: HTTP 404.
- Confirmação sem `last_refined_story`: HTTP 422.
- Falha na API do Jira: logada, exposta como HTTP 502.

## Integração com o Projeto
- `ConversationAgent` depende de `LLMClient`, que usa o SDK OpenAI apontado para a URL em `settings.llm_base_url` (suporta qualquer endpoint compatível com OpenAI).
- O estado da sessão é gerenciado por `app/services/session_store` (em memória; veja [Session Store](session-store.md)).
- Na confirmação, o sistema delega a criação do ticket para `app/integrations/jira.JiraClient`.
- `RefinedStory` é o contrato de dados compartilhado entre o sistema de conversação, o refinador avulso (`StoryRefinerAgent`) e a integração com o Jira.

## Limitações Atuais
- Sessões são armazenadas apenas em memória — são perdidas ao reiniciar o servidor.
- Sem expiração ou TTL de sessão: sessões acumulam indefinidamente até serem descartadas ou confirmadas explicitamente.
- O histórico completo é enviado a cada chamada ao LLM — o custo em tokens cresce linearmente com o tamanho da conversa.
- `_parse_conversation_response()` duplica a lógica de parsing JSON por chaves balanceadas já presente em `LLMClient._first_balanced_json_object()`.

## Pontos de Evolução Recomendados
- Adicionar expiração de sessão baseada em TTL para evitar crescimento ilimitado de memória.
- Consolidar o parsing de JSON em um utilitário compartilhado para eliminar a duplicação.
- Adicionar janelamento ou sumarização do histórico de conversa para limitar o uso de tokens em sessões longas.
- Persistir sessões em um store durável (Redis, banco de dados) para sobreviver a reinicializações do servidor.

## Referências
- Código-fonte: `app/agents/conversation_agent.py`, `app/prompts/conversation_system.txt`, `app/api/routes.py`
- Documentos relacionados: [Session Store](session-store.md)
