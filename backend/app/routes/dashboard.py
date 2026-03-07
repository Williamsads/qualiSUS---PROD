from flask import Blueprint, render_template, jsonify, session
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from app.database import get_connection

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route("/")
def index():
    if "user_id" not in session:
        return "Não autorizado. Por favor, faça login.", 401
    return render_template("dashboard.html")

@dashboard_bp.route("/api/stats")
def api_stats():
    if "user_id" not in session:
        return jsonify({"error": "Não autorizado"}), 401

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Altas (Discharges)
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM ciclo_cuidado 
            WHERE status IN ('ALTA', 'ENCERRADO_AUTOMATICO')
        """)
        altas = cur.fetchone()['total']

        # Faltas (No-shows)
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM agendamento_exames 
            WHERE status = 'NAO_COMPARECEU'
        """)
        faltas = cur.fetchone()['total']

        # Faltas sem Justificativa 
        # (Assuming for now that all status='NAO_COMPARECEU' without a specific 'reagendar' desfecho 
        # or just counting those in agendamento_exames that didn't result in a medical outcome)
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM agendamento_exames ae
            LEFT JOIN desfechos_clinicos dc ON ae.id = dc.atendimento_id
            WHERE ae.status = 'NAO_COMPARECEU' 
              AND (dc.tipo_desfecho IS NULL OR dc.tipo_desfecho != 'REAGENDADO')
        """)
        faltas_sem_justificativa = cur.fetchone()['total']

        # Atendimentos Realizados (Finalized/Realized)
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM agendamento_exames 
            WHERE status IN ('Realizado', 'Finalizado')
        """)
        realizados = cur.fetchone()['total']

        # Agendamentos para hoje
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM agendamento_exames 
            WHERE data_consulta = CURRENT_DATE
        """)
        hoje = cur.fetchone()['total']

        # Stats por Especialidade (Top 5)
        cur.execute("""
            SELECT especialidade, COUNT(*) as total 
            FROM agendamento_exames 
            GROUP BY especialidade 
            ORDER BY total DESC 
            LIMIT 5
        """)
        por_especialidade = cur.fetchall()

        # Evolução mensal (últimos 6 meses)
        cur.execute("""
            SELECT 
                TO_CHAR(data_consulta, 'YYYY-MM') as mes,
                COUNT(*) as total
            FROM agendamento_exames
            WHERE data_consulta >= CURRENT_DATE - interval '6 months'
            GROUP BY mes
            ORDER BY mes ASC
        """)
        evolucao = cur.fetchall()

        # Eficiência por Unidade
        # (Comparecimentos / Total Agendados que não foram cancelados)
        cur.execute("""
            SELECT 
                unidade,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status IN ('Realizado', 'Finalizado')) as realizados,
                ROUND(
                    (COUNT(*) FILTER (WHERE status IN ('Realizado', 'Finalizado'))::float / 
                    NULLIF(COUNT(*) FILTER (WHERE status NOT IN ('Cancelado')), 0)) * 100
                ) as eficiencia
            FROM agendamento_exames
            WHERE unidade IS NOT NULL
            GROUP BY unidade
            ORDER BY eficiencia DESC
        """)
        unidades = cur.fetchall()

        return jsonify({
            "altas": altas,
            "faltas": faltas,
            "faltas_sem_justificativa": faltas_sem_justificativa,
            "realizados": realizados,
            "hoje": hoje,
            "por_especialidade": por_especialidade,
            "evolucao": evolucao,
            "unidades": unidades
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()
