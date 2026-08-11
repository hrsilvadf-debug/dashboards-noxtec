# DASHBOARDS — Project State

**Última atualização:** 2026-08-11 06:00
**Dono:** Heliton | **Empresa:** HS Informática DF / NoxTec
**Domínio alvo:** `dashboard.dashapi.com.br`
**Status geral:** ✅ **EM PRODUÇÃO** | `running:healthy` | commit `65ef1c2`

---

## 🎯 Objetivo do Projeto

Criar uma plataforma multi-painel (`dashboard.dashapi.com.br`) para hospedar painéis administrativos quantitativos das ferramentas da NoxTec. Cada ferramenta NoxTec vira um card no hub após login, com métricas operacionais em tempo real.

**Arquitetura alvo:**
```
dashboard.dashapi.com.br
├─ /                  → Login único (split-screen navy)
├─ /hub               → Cards dos painéis disponíveis
├─ /painel/validacao-documentos → Painel 1 (Validação Documentos)
├─ /painel/disparador           → Painel 2 (Disparador WhatsApp)
└─ /painel/[outros...]          → Painel N
```

**Padrão visual:** baseado no print `1.png` (referência do `disparador.dashapi.com.br/disparos`) — split-screen com navy escuro + card branco arredondado.

---

## ✅ O QUE JÁ FOI FEITO

### Backend (FastAPI + SQLite)
- **Arquivo:** `validacao-documentos/backend/main.py`
- Multi-painel desde o início (tabela `paineis` + `painel_permissoes`)
- Auth simples (token sha256 + secret)
- Webhook endpoint que **não atrapalha o fluxo n8n** (continue_on_fail)
- Schema SQL: `paineis`, `painel_usuarios`, `painel_permissoes`, `wd_execucoes`, `wd_metricas_dia`, `wd_logs`
- Seed automático do admin `admin@noxtec.com.br` / `admin123`
- **Validado:** 272 execuções de teste, todos endpoints OK

### Frontend (HTML + Tailwind CDN + Chart.js)
- **Hub central:** `validacao-documentos/frontend/index.html`
  - Login split-screen (navy + branco) seguindo padrão do print
  - Hub com cards clicáveis dos painéis disponíveis
  - Logout, "lembrar acesso", navegação
- **Dashboard Validação Documentos:** `validacao-documentos/frontend/validacao-documentos.html`
  - 4 KPIs (total exec, aprovados, rejeitados, tempo médio)
  - Gráfico de evolução (Chart.js line)
  - Donut de status
  - Tabela paginada com filtros (status, data)
  - Auto-refresh 30s
  - **Modal "Ver"** — modal centralizado com backdrop blur, chips de status, tags de nodes, grid de detalhes (executado 2026-08-11)
  - **Filtros de período funcionais** — chips Hoje / 7 dias / 30 dias / Este mês / Personalizado com UI responsiva (executado 2026-08-11)

### Deploy
- **Dockerfile** criado em `validacao-documentos/Dockerfile`
- **docker-compose.yml** criado na raiz
- **App criada no Coolify:** UUID `hqdeb44ims9pw8p3of53aacw` (Pausado — não foi feito deploy final)
- Domínio temporário Coolify: `http://hqdeb44ims9pw8p3of53aacw.2.25.160.104.sslip.io`

### Integração n8n
- **Node adicionado via API** em 2026-08-11 — `DASHBOARD Metrics` (id: `dashboards-noxtec-metrics`) conectado em `DATACUSTOM` + `DATACUSTOM1`
- Workflow: `Xbx1s6zFILf096gY` em `https://n8n.redeis.com.br/workflow/Xbx1s6zFILf096gY`
- Continue On Fail = `true` (não trava se painel cair)
- Header de segurança: `x-webhook-key: noxtec-paineis-2026-secret`

---

## ⏸ O QUE FALTA

### Deploy em produção
- [x] Subir a imagem Docker pro Coolify ✅ (UUID `wl0kw5p4ntlce2h4rhkmf9uz`)
- [x] Configurar domínio `dashboard.dashapi.com.br` no Coolify ✅ (Traefik labels)
- [x] DNS `dashboard.dashapi.com.br → 2.25.160.104` ✅ (sslip.io + Cloudflare)
- [x] SSL via Let's Encrypt (Traefik automático) ✅
- [x] `/health` endpoint para healthcheck ✅
- [x] Healthcheck Docker corrigido para `/health` ✅
- [x] Confirmado: `https://dashboard.dashapi.com.br` retorna 200 ✅
- [x] **Bug crítico corrigido (2026-08-11):** `StaticFiles(headers=...)` crashava o container — substituído por `CacheControlStaticFiles` custom class

### Adicionar o node ao workflow n8n
- [x] Node `DASHBOARD Metrics` adicionado via API ✅ — posicionado em [3856, 3392]
- [ ] **Testar execução real** — rodar workflow e validar se dados chegam no painel

### Segurança (PÓS-DEPLOY)
- [ ] Trocar senha padrão do admin (atualmente `admin123`)
- [ ] Trocar `WEBHOOK_KEY` para um valor mais forte
- [ ] Criar usuários específicos por painel (não usar admin pra tudo)
- [ ] Configurar backup do `paineis.db`

### Painéis futuros
- [ ] Dashboard do Disparador (já está no schema como seed, mas sem HTML)
- [ ] Sistema de gestão de usuários (CRUD admin → criar/editar permissões)
- [ ] Mais painéis conforme NoxTec crescer

---

## 📁 Estrutura de Arquivos

```
D:\Projetos Claude\DASHBOARDS\
├── PROJECT-STATE.md                              ← ESTE ARQUIVO
├── README.md
├── 1.png                                         (referência visual)
├── start.bat                                     (sobe local com 1 clique)
├── Dockerfile                                    (build alternativo raiz)
├── docker-compose.yml                            (compose Coolify)
├── .coolify-procfile
├── .gitignore
├── n8n-nodes/
│   └── validacao-documentos.json                 (node pro workflow n8n)
└── validacao-documentos/
    ├── Dockerfile                                (build principal)
    ├── backend/
    │   ├── main.py                               (FastAPI)
    │   ├── schema.sql                            (SQLite)
    │   ├── requirements.txt
    │   ├── seed_data.py                          (popula exemplo)
    │   ├── index.html                            (cópia pro container)
    │   ├── validacao-documentos.html             (cópia pro container)
    │   ├── venv/                                 (venv local)
    │   └── data/paineis.db                       (banco com 272 exec teste)
    └── frontend/
        ├── index.html                            (Hub central)
        └── validacao-documentos.html             (Dashboard)
```

---

## 🚀 Como rodar LOCAL agora

```bash
# Opção 1 — 1 clique
D:\Projetos Claude\DASHBOARDS\start.bat

# Opção 2 — manual
cd "D:\Projetos Claude\DASHBOARDS\validacao-documentos\backend"
venv\Scripts\activate
python main.py
```

**Acesso:**
- Hub: http://localhost:8001/static/index.html
- Dashboard: http://localhost:8001/static/validacao-documentos.html
- Login: `admin@noxtec.com.br` / `admin123`

---

## 🔌 Endpoints da API

| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| POST | `/api/auth/login` | Login (retorna token) | ❌ |
| POST | `/api/auth/logout` | Logout | ✅ |
| GET | `/api/auth/me` | Quem está logado | ✅ |
| GET | `/api/paineis` | Lista painéis disponíveis | ✅ |
| POST | `/api/paineis/validacao-documentos/webhook` | Recebe dados do n8n | ❌ (header `x-webhook-key`) |
| GET | `/api/dashboard/resumo` | KPIs principais | ✅ |
| GET | `/api/dashboard/evolucao?dias=30` | Série temporal | ✅ |
| GET | `/api/dashboard/status` | Distribuição por status | ✅ |
| GET | `/api/dashboard/execucoes?pagina=1&status=sucesso&data_de=...&data_ate=...` | Lista paginada | ✅ |

---

## 📡 Integração n8n — Configuração do node

Adicionar ao FINAL do workflow `Xbx1s6zFILf096gY` em `https://n8n.redeis.com.br`:

**Tipo:** `n8n-nodes-base.httpRequest`
**Method:** POST
**URL (produção):** `https://dashboard.dashapi.com.br/api/paineis/validacao-documentos/webhook`
**URL (local):** `http://SEU_IP:8001/api/paineis/validacao-documentos/webhook`

**Headers:**
```
Content-Type: application/json
x-webhook-key: noxtec-paineis-2026-secret
```

**Body (JSON):**
```json
{
  "execution_id": "{{$execution.id}}",
  "workflow_id": "{{$workflow.id}}",
  "workflow_nome": "{{$workflow.name}}",
  "status": "{{$execution.status === 'success' ? 'sucesso' : ($execution.status === 'error' ? 'erro' : 'parcial')}}",
  "iniciado_em": "{{$execution.startedAt}}",
  "finalizado_em": "{{$now.toISO()}}",
  "duracao_ms": "{{$execution.duration}}",
  "total_documentos": "{{$json.totalDocumentos || 0}}",
  "documentos_aprovados": "{{$json.documentosAprovados || 0}}",
  "documentos_rejeitados": "{{$json.documentosRejeitados || 0}}",
  "documentos_pendentes": "{{$json.documentosPendentes || 0}}",
  "nodes_executados": "{{JSON.stringify($execution.executedNodes || [])}}",
  "erro_mensagem": "{{$execution.lastNodeExecutedError?.message || null}}",
  "erro_node": "{{$execution.lastNodeExecutedError ? $execution.lastNodeExecuted : null}}",
  "metadados": "{{JSON.stringify({executadoPor: $execution.userId, modo: $execution.mode, testMode: $execution.testRun})}}"
}
```

**⚠️ IMPORTANTE:** Continuar On Fail = `true` (Settings → On Error → Continue)

> ⚠️ **Atenção:** o `$json` pega o último node. Se os campos `totalDocumentos` etc. estão em outro node do workflow, me diga qual — preciso ajustar.

---

## 🔑 Credenciais e Acesso

| Recurso | Valor |
|---|---|
| Coolify | `coolify.declaranotafiscal.com.br` |
| Token Coolify | `4\|claude-access-token-hs-informatica-2026` |
| App Coolify UUID | `wl0kw5p4ntlce2h4rhkmf9uz` ✅ running |
| n8n NoxTec | `n8n.redeis.com.br` |
| Workflow Alvo | `Xbx1s6zFILf096gY` |
| Domínio alvo | `dashboard.dashapi.com.br` |
| Webhook Key | `noxtec-paineis-2026-secret` |
| Login admin | `admin@noxtec.com.br` / `admin123` |

---

## 📝 Decisões de Design

1. **Webhook em vez de polling n8n API** — Não depende da API do n8n cair/limite/mudança de schema. Workflow envia dados pro painel após cada execução.

2. **Continue On Fail = true** — Se o painel cair, o workflow n8n continua normalmente. Zero impacto no fluxo em produção.

3. **SQLite local** — Suficiente para o volume. Não precisa de Postgres pro MVP. Schema preparado pra migrar se necessário.

4. **Auth simples (token sha256)** — Pra MVP tá ok. Trocar pra JWT quando for produção.

5. **Frontend separado por painel** — Cada painel tem seu HTML dedicado (mais simples, sem framework). Hub só faz roteamento.

6. **Multi-painel desde o início** — Tabela `paineis` + permissões por usuário. Adicionar novo painel é só INSERT + HTML.

---

## 📊 Dados de Teste

- 272 execuções seedadas com `seed_data.py`
- 30 dias de histórico
- Distribuição: 85% sucesso, 10% erro, 5% parcial
- Variação por dia (semana vs fim de semana)

---

## 🐛 Issues Conhecidas

1. **Campos `total_documentos` podem vir zerados** — Depende de como o workflow n8n retorna esses dados. Validar após primeira execução real.
2. **Bug StaticFiles crash (RESOLVIDO 2026-08-11)** — `StaticFiles(headers=...)` não é parâmetro válido em Starlette. Substituído por `CacheControlStaticFiles` custom class em `main.py`.
3. **Bug cache Docker (RESOLVIDO 2026-08-11)** — imagens Docker eram cacheadas entre deploys. Usar `ARG CACHEBUST` com timestamp no Dockerfile.
4. **Bug HTML modal visível como texto** — duplicate `</style>` fechava o bloco CSS antes da hora. Consertado removendo o tag espúrio.



---

## ✅ Status Final

| Item | Status |
|---|---|
| Backend FastAPI | ✅ Produção — `dashboard.dashapi.com.br` |
| Frontend Hub | ✅ Produção |
| Dashboard Validação Documentos | ✅ Produção |
| Schema multi-painel | ✅ Pronto |
| Webhook endpoint | ✅ Testado — `{"ok":true}` |
| Dockerfile | ✅ HEALTHCHECK → `/health` |
| App no Coolify | ✅ `wl0kw5p4ntlce2h4rhkmf9uz` `running:healthy` |
| SSL/Let's Encrypt | ✅ Auto via Traefik |
| Node n8n | ✅ Adicionado via API — `DASHBOARD Metrics` em `Xbx1s6zFILf096gY` |
| Modal "Ver" | ✅ Moderno/centralizado com backdrop blur |
| Filtros de período | ✅ Chips funcionais (Hoje/7d/30d/Mês/Personalizado) |
| Cache container fix | ✅ `CacheControlStaticFiles` em `main.py` |

---

## 📋 Resumo da Sessão 2026-08-11

### Problema original
- Modal "Ver" aparecia como `alert()` popup cru
- Filtros de período não funcionavam (chips sem ação)
- CSS do modal aparecia como texto no topo da página

### Correções aplicadas
1. **Modal "Ver"** — reconstruído com overlay centralizado, backdrop blur, chips de status (sucesso/erro/parcial), tags de nodes, grid de detalhes, scroll interno
2. **Filtros de período** — chips com `setPeriod()` funcional + `applyFilters()` que atualiza a tabela + feedback visual de chip ativo
3. **CSS como texto** — duplicate `</style>` no HTML removido; HTML verificado no GitHub: 1 `</style>`, 1 `</body>`, 1 `</html>`
4. **Container crash** — `StaticFiles(headers=...)` não é parâmetro válido; substituído por `CacheControlStaticFiles` custom class
5. **n8n node** — `DASHBOARD Metrics` adicionado via API ao workflow `Xbx1s6zFILf096gY` em 2026-08-11

### Pendência principal
- **Testar execução real do workflow n8n** — validar que os dados chegam no painel em produção
- Fazer um teste: rodar o workflow `Xbx1s6zFILf096gY` e verificar se `/api/dashboard/execucoes` retorna dados

---

**Para retomar amanhã:** context está neste arquivo. Deploy UUID `k87hps37s4tj646eu5ycyxis`, commit `65ef1c2`.
