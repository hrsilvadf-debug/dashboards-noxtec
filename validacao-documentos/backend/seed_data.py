"""Popula banco com dados de exemplo para testar o dashboard."""
import sqlite3
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "paineis.db"
WEBHOOK_URL = "http://localhost:8001/api/paineis/validacao-documentos/webhook"

random.seed(42)
now = datetime.now()

print("Populando banco com dados de exemplo...")

# Gera 30 dias de dados
total = 0
for d in range(30, -1, -1):
    data = now - timedelta(days=d)
    # Variação: dias de semana têm mais volume
    is_weekend = data.weekday() >= 5
    n_execucoes = random.randint(2, 8) if is_weekend else random.randint(5, 15)

    for exec_n in range(n_execucoes):
        hora = random.randint(7, 20)
        minuto = random.randint(0, 59)
        iniciado   = data.replace(hour=hora, minute=minuto, second=0)
        duracao    = random.randint(30000, 600000)  # 30s a 10min
        finalizado = iniciado + timedelta(milliseconds=duracao)

        # 85% sucesso, 10% erro, 5% parcial
        r = random.random()
        status = "sucesso" if r < 0.85 else ("erro" if r < 0.95 else "parcial")
        total_docs = random.randint(10, 200)
        aprovados  = int(total_docs * random.uniform(0.7, 0.95)) if status != "erro" else int(total_docs * random.uniform(0.3, 0.6))
        rejeitados = total_docs - aprovados if status == "sucesso" else random.randint(0, max(1, int(total_docs*0.4)))
        pendentes  = max(0, total_docs - aprovados - rejeitados)

        exec_id = f"exec-{data.strftime('%Y%m%d')}-{exec_n:03d}"
        erro_msg = "Documento ilegível" if status == "erro" else None
        erro_node = "OCR" if status == "erro" else None

        conn = sqlite3.connect(str(DB_PATH), timeout=10)
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
                exec_id, "Xbx1s6zFILf096gY", "Validação Documentos",
                status, iniciado.isoformat(), finalizado.isoformat(),
                duracao, total_docs, aprovados, rejeitados, pendentes,
                json.dumps({"populado": True}), erro_msg, erro_node,
                json.dumps([{"nome":"webhook"},{"nome":"ocr"},{"nome":"validar"}]),
                json.dumps({}),
            ))

            # Métricas do dia
            data_str = data.strftime("%Y-%m-%d")
            conn.execute("INSERT INTO wd_metricas_dia (data) VALUES (?) ON CONFLICT(data) DO UPDATE SET data = data", (data_str,))
            # Recalcula do zero para evitar dupla contagem se rodar duas vezes
            conn.execute("DELETE FROM wd_metricas_dia WHERE data = ?", (data_str,))
            conn.execute("""
                INSERT INTO wd_metricas_dia
                (data, total_execucoes, total_sucesso, total_erro, total_documentos,
                 docs_aprovados, docs_rejeitados, tempo_medio_ms)
                SELECT
                    date(finalizado_em) as d,
                    COUNT(*),
                    SUM(CASE WHEN status='sucesso' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN status='erro'    THEN 1 ELSE 0 END),
                    COALESCE(SUM(total_documentos), 0),
                    COALESCE(SUM(documentos_aprovados), 0),
                    COALESCE(SUM(documentos_rejeitados), 0),
                    COALESCE(AVG(duracao_ms), 0)
                FROM wd_execucoes WHERE date(finalizado_em) = ?
                GROUP BY date(finalizado_em)
            """, (data_str,))
            conn.commit()
            total += 1
        finally:
            conn.close()

print(f"[OK] {total} execucoes populadas em {DB_PATH}")
