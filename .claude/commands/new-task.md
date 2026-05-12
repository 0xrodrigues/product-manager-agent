---
description: Cria uma nova tarefa de desenvolvimento no banco de dados SQLite e gera o arquivo TASK.md correspondente. Use quando o usuário solicitar o desenvolvimento de uma nova feature, correção ou melhoria.
---

Crie uma nova tarefa de desenvolvimento para: $ARGUMENTS

## Processo

1. Extraia o título da tarefa a partir de `$ARGUMENTS`. Se `$ARGUMENTS` contiver uma descrição mais longa, use a primeira frase ou ideia principal como título e o restante como contexto para preencher o Objetivo.

2. Registre a tarefa no banco de dados executando:
   ```bash
   python -c "import task_manager; import json; t = task_manager.create_task('<TITULO>'); print(json.dumps(t))"
   ```
   Capture o `id`, `description` (caminho do arquivo) e `started_at` do resultado.

3. Crie o diretório da tarefa se não existir:
   ```bash
   mkdir -p <caminho_do_diretório>
   ```

4. Leia o template em `.claude/new-task/TASK_TEMPLATE.md` e crie o arquivo `task.md` no caminho retornado pelo banco (`description`), substituindo os placeholders:
   - `[TITULO]` → título extraído
   - `[ID]` → uuid retornado
   - `[DATA]` → data de hoje (AAAA-MM-DD)
   - `[CAMINHO]` → caminho `description` retornado pelo banco

5. Preencha a seção **Objetivo** com o contexto extraído de `$ARGUMENTS`.

6. Exiba um resumo confirmando:
   - ID da tarefa
   - Status: PLANNED
   - Arquivo criado: caminho do `task.md`

## Restrições

- Nunca altere arquivos fora de `docs/tasks/` e `task_management.db`
- Sempre use `task_manager.py` para registrar — nunca insira diretamente no banco
- O título deve ser conciso (até 60 caracteres); descrições longas vão para o Objetivo
- Idioma do `task.md`: português
