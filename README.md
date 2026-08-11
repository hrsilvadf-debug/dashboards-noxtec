# DASHBOARDS NoxTec — Painéis Administrativos

> 📋 **Para estado completo do projeto, decisões, credenciais e próximos passos, leia `PROJECT-STATE.md`**

**Domínio alvo:** `dashboard.dashapi.com.br`

Sistema multi-painel para métricas operacionais das ferramentas NoxTec. Cada ferramenta vira um card no hub após login.

## Arquitetura

```
dashboard.dashapi.com.br
├─ /                  → Login único (split-screen navy)
├─ /hub               → Cards de painéis disponíveis
├─ /painel/validacao-documentos → Painel 1 (Validação Documentos)
├─ /painel/disparador           → Painel 2 (Disparador WhatsApp)
└─ /painel/[outros...]          → Painel N
```

Cada painel tem seu próprio webhook no n8n:
```
n8n workflow Xbx1s6zFILf096gY
  └─► POST https://dashboard.dashapi.com.br/api/paineis/validacao-documentos/webhook
```

## Stack

- **Backend:** FastAPI + SQLite
- **Frontend:** HTML + Tailwind CDN + Chart.js
- **Auth:** Token simples (sha256 + secret key)
- **Dados:** Recebidos via webhook do n8n

## Estrutura

```
DASHBOARDS/
├── PROJECT-STATE.md          ← ESTADO COMPLETO (leia primeiro!)
├── README.md                 ← este arquivo
├── 1.png                     (referência visual)
├── start.bat                 (sobe local com 1 clique)
├── Dockerfile
├── docker-compose.yml
├── n8n-nodes/
│   └── validacao-documentos.json     (node pro n8n)
└── validacao-documentos/
    ├── Dockerfile
    ├── backend/              (FastAPI + SQLite)
    │   ├── main.py
    │   ├── schema.sql
    │   ├── seed_data.py
    │   ├── requirements.txt
    │   ├── index.html
    │   ├── validacao-documentos.html
    │   └── data/paineis.db
    └── frontend/             (Hub + Dashboard)
        ├── index.html
        └── validacao-documentos.html
```

## Setup rápido (local)

```bash
# Opção 1 — 1 clique
start.bat

# Opção 2 — manual
cd validacao-documentos/backend
python -m venv venv
venv\Scripts\activate
pip install --only-binary=:all: fastapi pydantic uvicorn
python main.py
```

Acesse:
- Hub: http://localhost:8001/static/index.html
- Login: `admin@noxtec.com.br` / `admin123`

## Como adicionar novo painel

1. Inserir na tabela `paineis`:
```sql
INSERT INTO paineis (slug, nome, descricao, icone, cor_primaria)
VALUES ('nome-do-painel', 'Nome', 'Descrição', '🎯', '#4F46E5');
```

2. Criar rota webhook em `main.py`:
```python
@app.post("/api/paineis/{slug}/webhook")
def webhook(payload): ...
```

3. Criar rotas de dashboard em `main.py`:
```python
@app.get("/api/dashboard/{slug}/resumo") ...
```

4. Adicionar arquivo HTML do painel em `frontend/`

## Próximos passos

Veja `PROJECT-STATE.md` para status detalhado e próximos passos do deploy.
