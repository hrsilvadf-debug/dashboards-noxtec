"""
PRINTS NoxTec — Backend FastAPI Multi-Painel
Domínio: dashboard.dashapi.com.br
Painel: Validação Documentos
"""

import os
import sqlite3
import json
import hashlib
import secrets
from datetime import datetime, date, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Header, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List

# ============================================================
# CONFIGURAÇÃO
# ============================================================
BASE_DIR    = Path(__file__).parent
DATA_DIR    = BASE_DIR / "data"
FRONT_DIR   = BASE_DIR / "frontend"
DB_PATH     = DATA_DIR / "paineis.db"
WEBHOOK_KEY = os.environ.get("WEBHOOK_KEY", "noxtec-paineis-2026-secret")

DATA_DIR.mkdir(exist_ok=True)

# ============================================================
# DATABASE HELPERS
# ============================================================
def get_db():
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript((BASE_DIR / "schema.sql").read_text(encoding="utf-8"))
    conn.commit()
    conn.close()

def row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, str) and (v.startswith("{") or v.startswith("[")):
            try:
                d[k] = json.loads(v)
            except:
                pass
    return d

# ============================================================
# PYDANTIC MODELS
# ============================================================
class LoginRequest(BaseModel):
    email: str
    senha: str

class TokenResponse(BaseModel):
    token:     str
    nome:      str
    email:     str
    nivel:     str
    paineis:   list  # slugs que o usuário tem acesso
    expira_em: int

class WebhookPayload(BaseModel):
    execution_id:             str
    workflow_id:              Optional[str] = None
    workflow_nome:            Optional[str] = None
    status:                   str
    iniciado_em:              Optional[str] = None
    finalizado_em:            Optional[str] = None
    duracao_ms:               Optional[int] = None
    total_documentos:         Optional[int] = 0
    documentos_aprovados:     Optional[int] = 0
    documentos_rejeitados:    Optional[int] = 0
    documentos_pendentes:     Optional[int] = 0
    metadados:                Optional[dict] = {}
    erro_mensagem:            Optional[str] = None
    erro_node:                Optional[str] = None
    nodes_executados:         Optional[List[dict]] = []
    dados_originais:          Optional[dict] = {}

# ============================================================
# APP
# ============================================================
app = FastAPI(title="PRINTS NoxTec", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Healthcheck (sempre 200, sem auth) ──
@app.get("/health")
def health():
    return {"status": "ok", "service": "prints-dashboard"}

# Servir frontend estático
if FRONT_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONT_DIR), headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}), name="static")
elif (BASE_DIR / "index.html").exists():
    # Quando frontend files estão copiados direto no backend
    app.mount("/static", StaticFiles(directory=str(BASE_DIR), headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}), name="static")

# ============================================================
# AUTH
# ============================================================
tokens = {}

def hash_senha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def verify_token(authorization: str = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente")
    token = authorization.replace("Bearer ", "")
    if token not in tokens:
        raise HTTPException(status_code=401, detail="Token inválido")
    if tokens[token]["expira"] < int(datetime.now().timestamp()):
        raise HTTPException(status_code=401, detail="Sessão expirada")
    return tokens[token]

@app.post("/api/auth/login", response_model=TokenResponse)
def login(body: LoginRequest):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM painel_usuarios WHERE email = ? AND ativo = 1",
        (body.email,)
    ).fetchone()
    if not user or user["senha_hash"] != hash_senha(body.senha):
        conn.close()
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    perms = conn.execute("""
        SELECT p.slug, pp.nivel FROM painel_permissoes pp
        JOIN paineis p ON p.id = pp.painel_id
        WHERE pp.usuario_id = ? AND p.ativo = 1
    """, (user["id"],)).fetchall()
    conn.close()
    expires = int((datetime.now() + timedelta(hours=8)).timestamp())
    token = secrets.token_urlsafe(32)
    tokens[token] = {"email": user["email"], "nivel": user["nivel"], "expira": expires}
    return TokenResponse(
        token=token, nome=user["nome"], email=user["email"],
        nivel=user["nivel"], paineis=[dict(p) for p in perms], expira_em=expires
    )

@app.post("/api/auth/logout")
def logout(authorization: str = Header(None)):
    if authorization:
        tokens.pop(authorization.replace("Bearer ", ""), None)
    return {"ok": True}

@app.get("/api/auth/me")
def me(user: dict = Depends(verify_token)):
    return user

# ============================================================
# PAINÉIS (multi)
# ============================================================
@app.get("/api/paineis")
def listar_paineis(user: dict = Depends(verify_token)):
    conn = get_db()
    rows = conn.execute("SELECT * FROM paineis WHERE ativo = 1 ORDER BY nome").fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]

# ============================================================
# WEBHOOK — Validação Documentos
# ============================================================
@app.post("/api/paineis/validacao-documentos/webhook")
def webhook(payload: WebhookPayload, x_webhook_key: str = Header(None)):
    if x_webhook_key != WEBHOOK_KEY:
        return JSONResponse(status_code=403, content={"erro": "Chave inválida"})

    conn = get_db()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO wd_execucoes (
                execution_id, workflow_id, workflow_nome, status,
                iniciado_em, finalizado_em, duracao_ms,
                total_documentos, documentos_aprovados, documentos_rejeitados,
                documentos_pendentes, metadados, erro_mensagem, erro_node,
                nodes_executados, dados_originais
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            payload.execution_id, payload.workflow_id, payload.workflow_nome,
            payload.status, payload.iniciado_em, payload.finalizado_em,
            payload.duracao_ms, payload.total_documentos,
            payload.documentos_aprovados, payload.documentos_rejeitados,
            payload.documentos_pendentes, json.dumps(payload.metadados or {}),
            payload.erro_mensagem, payload.erro_node,
            json.dumps(payload.nodes_executados or []),
            json.dumps(payload.dados_originais or {}),
        ))

        if payload.finalizado_em:
            data = payload.finalizado_em[:10]
            conn.execute("INSERT INTO wd_metricas_dia (data) VALUES (?) ON CONFLICT(data) DO UPDATE SET data = data", (data,))
            conn.execute("""
                UPDATE wd_metricas_dia SET
                    total_execucoes  = total_execucoes + 1,
                    total_documentos = total_documentos + ?,
                    docs_aprovados   = docs_aprovados + ?,
                    docs_rejeitados  = docs_rejeitados + ?,
                    tempo_medio_ms   = CASE WHEN total_execucoes = 0 THEN ?
                                          ELSE (tempo_medio_ms * total_execucoes + ?) / (total_execucoes + 1) END,
                    total_sucesso    = total_sucesso + CASE WHEN ? = 'sucesso' THEN 1 ELSE 0 END,
                    total_erro       = total_erro    + CASE WHEN ? = 'erro'    THEN 1 ELSE 0 END,
                    updated_at       = CURRENT_TIMESTAMP
                WHERE data = ?
            """, (
                payload.total_documentos or 0,
                payload.documentos_aprovados or 0,
                payload.documentos_rejeitados or 0,
                payload.duracao_ms or 0, payload.duracao_ms or 0,
                payload.status, payload.status, data
            ))
        conn.commit()
        return {"ok": True, "execution_id": payload.execution_id}
    except Exception as e:
        conn.rollback()
        return JSONResponse(status_code=500, content={"erro": str(e)})
    finally:
        conn.close()

# ============================================================
# DASHBOARD — Validação Documentos
# ============================================================
@app.get("/api/dashboard/resumo")
def resumo(user: dict = Depends(verify_token)):
    conn = get_db()
    hoje = date.today()
    mes_inicio = hoje.replace(day=1).isoformat()

    totais = conn.execute("""
        SELECT COUNT(*) AS total_execucoes,
               SUM(CASE WHEN status='sucesso' THEN 1 ELSE 0 END) AS total_sucesso,
               SUM(CASE WHEN status='erro'    THEN 1 ELSE 0 END) AS total_erro,
               SUM(total_documentos)        AS total_documentos,
               SUM(documentos_aprovados)     AS total_aprovados,
               SUM(documentos_rejeitados)    AS total_rejeitados,
               AVG(duracao_ms)              AS tempo_medio_ms
        FROM wd_execucoes
    """).fetchone()

    mes = conn.execute("""
        SELECT COUNT(*) AS execucoes_mes,
               SUM(total_documentos) AS docs_mes,
               SUM(documentos_aprovados) AS aprovados_mes
        FROM wd_execucoes WHERE finalizado_em >= ?
    """, (mes_inicio,)).fetchone()

    Hoje = conn.execute("""
        SELECT COUNT(*) AS execucoes_hoje,
               SUM(total_documentos) AS docs_hoje
        FROM wd_execucoes WHERE date(finalizado_em) = ?
    """, (hoje.isoformat(),)).fetchone()

    conn.close()
    return {
        "geral": dict(totais),
        "mes":   dict(mes),
        "hoje":  dict(Hoje),
    }

@app.get("/api/dashboard/evolucao")
def evolucao(dias: int = Query(default=30, ge=7, le=365), user: dict = Depends(verify_token)):
    conn = get_db()
    inicio = (date.today() - timedelta(days=dias)).isoformat()
    rows = conn.execute("""
        SELECT data, total_execucoes, total_documentos,
               docs_aprovados, docs_rejeitados, tempo_medio_ms
        FROM wd_metricas_dia WHERE data >= ? ORDER BY data ASC
    """, (inicio,)).fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]

@app.get("/api/dashboard/execucoes")
def execucoes(
    pagina:     int = Query(default=1, ge=1),
    por_pagina: int = Query(default=20, ge=1, le=100),
    status:     Optional[str] = None,
    data_de:    Optional[str] = None,
    data_ate:   Optional[str] = None,
    user: dict = Depends(verify_token)
):
    conn = get_db()
    offset = (pagina - 1) * por_pagina
    where, params = [], []
    if status:   where.append("status = ?");          params.append(status)
    if data_de:  where.append("finalizado_em >= ?");  params.append(data_de)
    if data_ate: where.append("finalizado_em <= ?");  params.append(data_ate)
    sql_where = ("WHERE " + " AND ".join(where)) if where else ""

    total = conn.execute(f"SELECT COUNT(*) AS c FROM wd_execucoes {sql_where}", params).fetchone()["c"]
    rows  = conn.execute(f"""
        SELECT * FROM wd_execucoes {sql_where}
        ORDER BY finalizado_em DESC LIMIT ? OFFSET ?
    """, (*params, por_pagina, offset)).fetchall()
    conn.close()
    return {
        "total": total, "pagina": pagina, "por_pagina": por_pagina,
        "items": [row_to_dict(r) for r in rows]
    }

@app.get("/api/dashboard/status")
def status_dist(user: dict = Depends(verify_token)):
    conn = get_db()
    rows = conn.execute("""
        SELECT status, COUNT(*) AS quantidade, SUM(total_documentos) AS documentos
        FROM wd_execucoes GROUP BY status
    """).fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]

# ============================================================
# INIT + USUÁRIO ADMIN PADRÃO
# ============================================================
init_db()

def seed_admin():
    conn = get_db()
    existe = conn.execute("SELECT id FROM painel_usuarios WHERE email = 'admin@noxtec.com.br'").fetchone()
    if not existe:
        conn.execute("""
            INSERT INTO painel_usuarios (email, senha_hash, nome, nivel)
            VALUES (?, ?, ?, ?)
        """, ("admin@noxtec.com.br", hash_senha("admin123"), "Administrador NoxTec", "admin"))
        admin_id = conn.execute("SELECT id FROM painel_usuarios WHERE email = 'admin@noxtec.com.br'").fetchone()["id"]
        paineis = conn.execute("SELECT id FROM paineis").fetchall()
        for p in paineis:
            conn.execute("INSERT OR IGNORE INTO painel_permissoes (usuario_id, painel_id, nivel) VALUES (?, ?, 'admin')", (admin_id, p["id"]))
        conn.commit()
    conn.close()

seed_admin()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 80))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port, reload=False)
