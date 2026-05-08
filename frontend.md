# Frontend — PM Agent

## Prompt para o Claude Code

Adicione um frontend estático ao projeto `product-manager-agent`, dentro do mesmo repositório do backend.

---

## Estrutura esperada

Crie a pasta `frontend/` na raiz do projeto com a seguinte estrutura:

```
frontend/
├── index.html
├── css/
│   └── styles.css
├── js/
│   └── app.js
└── README.md
```

Separe o HTML, CSS e JS em arquivos distintos. O `index.html` deve apenas referenciar os outros arquivos.

---

## Interface

Interface de chat inspirada no Claude/ChatGPT. Dark theme com a paleta oficial da Cielo:

- Azul principal: `#00aeef`
- Background: `#0a0a0a`
- Superfícies: `#111318`, `#181c22`, `#1e2229`
- Fonte: DM Sans (Google Fonts)

A tela deve ter:

- Header com nome "PM Agent · Cielo" e indicador de status
- Área de chat com histórico de mensagens
- Tela inicial com exemplos clicáveis quando não há conversa ativa
- Cada resposta do agente renderiza um story card com: título, story points, user story, requisitos funcionais, regras de negócio, critérios de aceite e dependências
- Botões "Criar no Jira" e "Descartar" em cada story card
- Indicador de digitação (três pontos animados) enquanto aguarda resposta da API
- Textarea com auto-resize e atalho Enter para enviar / Shift+Enter para nova linha

---

## Endpoints utilizados

```
POST   /api/stories/session                      → inicia sessão
                                                   body: { title, description }

POST   /api/stories/session/{session_id}         → continua conversa
                                                   body: { message }

POST   /api/stories/session/{session_id}/confirm → aprova e cria ticket no Jira

DELETE /api/stories/session/{session_id}         → descarta sessão
```

A constante `API_BASE` no `app.js` deve ser `http://localhost:8000/api`.

---

## CORS no backend

Em `app/main.py`, adicione o middleware CORS do FastAPI para aceitar requisições do frontend local:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Servir o frontend via FastAPI

Em `app/main.py`, configure o FastAPI para servir os arquivos estáticos da pasta `frontend/`:

```python
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
```

Isso deve ser feito **após** o registro de todos os routers, para não conflitar com as rotas da API.

---

## Observações

- Não use frameworks JS (React, Vue, etc.) — HTML/CSS/JS puro apenas
- Não use bibliotecas externas além do Google Fonts
- O `README.md` dentro de `frontend/` deve explicar como rodar o projeto completo
- Não altere nenhum arquivo de lógica do backend além do `app/main.py`