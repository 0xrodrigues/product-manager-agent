---
description: Gera e atualiza documentação técnica padronizada com metadados obrigatórios (data de criação, última atualização, versão). Use quando o usuário solicitar documentação técnica, explicações técnicas ou análise de comportamento de módulos/fluxos.
---

Gere ou atualize um documento técnico padronizado para: $ARGUMENTS

## Regras

1. Salve todos os documentos em `docs/memory/technical-documents/` usando nomes em kebab-case (ex.: `session-manager.md`, `prompt-assembly-flow.md`)
2. Use a estrutura de template definida em `.claude/technical-documentation/DOC_TEMPLATE.md`
3. Sempre inclua os metadados obrigatórios:
   - `Data de criação`: data de hoje (AAAA-MM-DD) — mantenha a original ao atualizar
   - `Última atualização`: data de hoje
   - `Versão do documento`: inicie em `1.0.0`; incremente seguindo semver nas atualizações:
     - `major`: grande mudança estrutural de escopo
     - `minor`: novas seções ou expansão relevante de comportamento
     - `patch`: pequenos ajustes, correções de texto ou refinamentos

## Processo

1. Identifique o que precisa ser documentado (arquivo, módulo, fluxo ou serviço)
2. Leia os arquivos-fonte relevantes com atenção — entenda o comportamento real, não o desejado
3. Mapeie componentes, entradas, saídas e casos de erro
4. Verifique se já existe um documento em `docs/memory/technical-documents/` — se sim, trate como atualização com incremento de versão
5. Preencha o template apenas com comportamento real (sem especulação)
6. Valide que todas as referências de código, endpoints e modelos mencionados são precisas
7. Escreva o documento final em `docs/memory/technical-documents/<nome-do-assunto>.md`

## Restrições Principais

- **Localização:** somente em `docs/memory/technical-documents/`
- **Template:** sempre siga a estrutura de `.claude/technical-documentation/DOC_TEMPLATE.md`
- **Metadados:** nunca omita data de criação, última atualização ou versão
- **Precisão:** documente apenas o comportamento observado no código — não o comportamento pretendido ou especulativo
- **Escopo:** um tópico focado por arquivo
- **Idioma:** toda a documentação deve ser escrita em português
