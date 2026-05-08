# product-manager-agent

## O que é

Um agente de IA que ajuda PMs a refinarem e criarem histórias de usuário no Jira. O PM descreve uma funcionalidade em texto livre e o agente devolve um ticket estruturado, criando-o automaticamente no Jira.

---

## O problema

PMs perdem tempo transformando ideias brutas em tickets bem escritos. O processo de escrever descrição, requisitos funcionais, regras de negócio e critérios de aceite é repetitivo e frequentemente inconsistente entre histórias.

---

## A proposta

O PM escreve o que quer — pode ser uma frase, um parágrafo, uma transcrição de reunião — e o agente:

1. Interpreta o input
2. Gera uma história estruturada com descrição, requisitos funcionais, regras de negócio e critérios de aceite
3. Cria o ticket no Jira automaticamente

Futuramente, o agente também vai cruzar a documentação interna do Confluence para enriquecer o contexto das histórias geradas.

---

## Stack

- **Python** como linguagem principal
- **FastAPI** para expor o agente como serviço HTTP
- **OpenAI** como LLM provider inicial (com intenção de migrar para Anthropic)
- **Jira API** para criação e edição de tickets
- Piloto rodando no projeto **PSCC**

---

## O que ainda não está definido

- Template padrão de histórias de usuário da empresa
- Campos obrigatórios do ticket além da descrição
- Formato dos critérios de aceite (BDD, checklist, texto livre)