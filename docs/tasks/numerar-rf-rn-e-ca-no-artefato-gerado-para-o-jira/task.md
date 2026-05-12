# Numerar RF, RN e CA no artefato gerado para o Jira

## Metadados
- ID: 5961cad7-2d16-454c-a52d-8539736f9033
- Status: PLANNED
- Data de início: 2026-05-12
- Caminho: docs/tasks/numerar-rf-rn-e-ca-no-artefato-gerado-para-o-jira/task.md

## Objetivo

Adicionar numeração sequencial aos itens de Requisitos Funcionais (RF), Regras de Negócio (RN) e Critérios de Aceite (CA) no artefato final enviado ao Jira. Atualmente os itens são gerados sem identificadores, o que dificulta rastreabilidade e referência cruzada durante o refinamento e desenvolvimento.

Exemplo do formato esperado:
- **RF-01**: Permitir cadastro inicial do novo usuário pelo app mobile.
- **RN-01**: O onboarding é destinado apenas a usuários que se cadastram pelo app mobile.
- **CA-01**: Dado que um novo usuário iniciou o cadastro no app mobile, Quando ele concluir o cadastro inicial, Então o sistema deve permitir avançar para o envio de documento.

A numeração deve ser gerada automaticamente pelo sistema — nem o LLM nem o usuário devem precisar fazê-la manualmente.

## Requisitos

- [ ] Identificar onde a montagem do artefato final ocorre (prompts e/ou pós-processamento)
- [ ] Garantir que `functional_requirements` seja prefixado com `RF-01`, `RF-02`, ...
- [ ] Garantir que `business_rules` seja prefixado com `RN-01`, `RN-02`, ...
- [ ] Garantir que `acceptance_criteria` seja prefixado com `CA-01`, `CA-02`, ...
- [ ] A numeração deve ser aplicada antes da montagem do payload enviado ao Jira
- [ ] Não quebrar o schema atual do modelo `RefinedStory`

## Critérios de Aceitação

- [ ] Um ticket criado no Jira exibe RF-01, RF-02... nos Requisitos Funcionais
- [ ] Um ticket criado no Jira exibe RN-01, RN-02... nas Regras de Negócio
- [ ] Um ticket criado no Jira exibe CA-01, CA-02... nos Critérios de Aceite
- [ ] Itens que já contenham prefixo não recebem numeração duplicada
- [ ] Nenhum outro campo do artefato é alterado

## Escopo

- **Inclui:** lógica de prefixação dos itens antes do envio ao Jira; possível ajuste nos prompts caso a numeração precise ser instruída ao LLM
- **Não inclui:** alteração no schema de `RefinedStory` em banco/memória; mudança na interface de conversação

## Arquivos Envolvidos

- [app/services/jira.py](../../../app/services/jira.py): ponto de criação do ticket — local mais provável para aplicar a numeração via pós-processamento
- [app/prompts/conversation_system.txt](../../../app/prompts/conversation_system.txt): instrui o LLM sobre o formato dos campos `functional_requirements`, `business_rules`, `acceptance_criteria`
- [app/prompts/interview_system.txt](../../../app/prompts/interview_system.txt): mesma instrução para o fluxo de entrevista
- [app/agents/conversation_agent.py](../../../app/agents/conversation_agent.py): orquestra o fluxo de refinamento e repassa a história ao Jira
- [app/agents/interview_agent.py](../../../app/agents/interview_agent.py): orquestra o fluxo de entrevista e repassa a história ao Jira

## Notas de Implementação

A abordagem preferida é **pós-processamento em `jira.py`** (ou em um helper chamado por ele), pois:
1. O LLM pode variar a formatação — depender do prompt para gerar os prefixos é frágil.
2. Centralizar em `_build_payload` ou em uma função `_number_items(items, prefix)` garante consistência independente do agente usado.
3. Não altera o contrato interno do modelo `RefinedStory`, que continua sem prefixos em memória/sessão.

Fluxo esperado:
```
RefinedStory (sem prefixos) → JiraClient._build_payload → _number_items() → payload com RF/RN/CA numerados → Jira API
```
