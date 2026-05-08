# PM Agent · Frontend

Interface de chat para o Product Manager Agent da Cielo.

## Como rodar

```bash
# 1. Instale as dependências do backend (uma vez)
cd ..
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas chaves

# 3. Suba o servidor
uvicorn app.main:app --reload --port 8000
```

O frontend é servido automaticamente em `http://localhost:8000`.

## Estrutura

```
frontend/
├── index.html      # Entrada — só referencia CSS e JS
├── css/styles.css  # Estilos (dark theme Cielo)
├── js/app.js       # Lógica de chat e integração com a API
└── README.md
```

## Endpoints consumidos

| Método | Rota | Ação |
|--------|------|------|
| POST | `/api/stories/session` | Inicia sessão com título e descrição |
| POST | `/api/stories/session/{id}` | Continua a conversa |
| POST | `/api/stories/session/{id}/confirm` | Aprova e cria ticket no Jira |
| DELETE | `/api/stories/session/{id}` | Descarta a sessão |
