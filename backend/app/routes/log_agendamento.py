from flask import Blueprint, render_template, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor

bp_agendamento = Blueprint(
    "log_agendamento",
    __name__,
    url_prefix="/log_agendamento"
)

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

@bp_agendamento.route("/")
def index():
    return render_template("log_agendamento.html")

@bp_agendamento.route("/api/atualizar/<int:id>", methods=["POST"])
def api_atualizar(id):
    data = request.json
    status = data.get("status")
    observacao = data.get("observacao")
    
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE agendamento_exames 
            SET status = %s, observacao = %s, atualizado_em = NOW()
            WHERE id = %s
        """, (status, observacao, id))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@bp_agendamento.route("/api/lista")
def api_lista():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT 
                ae.id,
                ae.status,
                t.nome_completo as paciente,
                t.cpf as cpf_paciente,
                vt.numero_funcional as num_func_vinculo, 
                t.telefone,
                ae.especialidade,
                f.nome as medico,
                TO_CHAR(ae.data_consulta, 'YYYY-MM-DD') as data,
                TO_CHAR(ae.horario, 'HH24:MI') as horario,
                ae.unidade,
                ae.observacao
            FROM agendamento_exames ae
            JOIN trabalhadores t ON ae.trabalhador_id = t.id
            JOIN funcionarios f ON ae.funcionario_id = f.id
            LEFT JOIN vinculos_trabalhadores vt ON ae.vinculo_id = vt.id
            ORDER BY ae.data_consulta DESC, ae.horario DESC
        """)
        rows = cur.fetchall()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@bp_agendamento.route("/api/deletar/<int:id>", methods=["DELETE"])
def api_deletar(id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM agendamento_exames WHERE id = %s", (id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()
