from flask import Blueprint, render_template, jsonify, request, session
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

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
    user_email = session.get("email")
    user_tipo = session.get("tipo")
    servidor_id = None
    
    if user_email:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM funcionarios WHERE email = %s", (user_email,))
        row = cur.fetchone()
        if row:
            servidor_id = row[0]
        cur.close()
        conn.close()

    return render_template("log_agendamento.html", user_tipo=user_tipo, servidor_id=servidor_id)

@bp_agendamento.route("/atendimento/<int:id>")
def atendimento(id):
    if "user_id" not in session:
        return redirect("/index")
        
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT 
            ae.*,
            t.nome_completo as paciente,
            t.cpf as cpf_paciente,
            vt.numero_funcional as num_func_vinculo,
            t.telefone,
            f.nome as medico
        FROM agendamento_exames ae
        JOIN trabalhadores t ON ae.trabalhador_id = t.id
        JOIN funcionarios f ON ae.funcionario_id = f.id
        LEFT JOIN vinculos_trabalhadores vt ON ae.vinculo_id = vt.id
        WHERE ae.id = %s
    """, (id,))
    
    appt = cur.fetchone()
    cur.close()
    conn.close()
    
    if not appt:
        flash("Agendamento não encontrado.", "erro")
        return redirect(url_for("log_agendamento.index"))
        
    return render_template("atendimento_clinico.html", appt=appt)

@bp_agendamento.route("/api/atualizar/<int:id>", methods=["POST"])
def api_atualizar(id):
    data = request.json
    status = data.get("status")
    observacao = data.get("observacao")
    desfecho = data.get("desfecho")  # 'nao_compareceu', 'reagendar', 'atendido'
    apto_psico = data.get("apto_psico") # True/False
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Busca dados atuais do agendamento
        cur.execute("SELECT * FROM agendamento_exames WHERE id = %s", (id,))
        appt = cur.fetchone()
        if not appt:
            return jsonify({"success": False, "error": "Agendamento não encontrado"}), 404

        user_email = session.get("email") or "Sistema"
        
        # --- REGRAS DE NEGÓCIO DE ACOLHIMENTO ---
        final_status = status
        validado = False

        if appt['especialidade'] == 'Acolhimento' and desfecho:
            if desfecho == 'nao_compareceu':
                final_status = 'NAO_COMPARECEU'
            
            elif desfecho == 'reagendar':
                # Gera novo agendamento automaticamente (+7 dias no mesmo horário)
                nova_data = appt['data_consulta'] + timedelta(days=7)
                cur.execute("""
                    INSERT INTO agendamento_exames 
                    (trabalhador_id, vinculo_id, funcionario_id, data_consulta, horario, unidade, especialidade, status, observacao, atualizado_por)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    appt['trabalhador_id'], appt['vinculo_id'], appt['funcionario_id'], 
                    nova_data, appt['horario'], appt['unidade'], appt['especialidade'], 
                    'Agendado', f"Reagendamento automático do ID {id}", user_email
                ))
            
            elif desfecho == 'atendido':
                final_status = 'Finalizado'
                if apto_psico is True:
                    validado = True
                    # Cria ciclo_cuidado ATIVO
                    cur.execute("""
                        INSERT INTO ciclo_cuidado (trabalhador_id, status)
                        VALUES (%s, 'ATIVO')
                    """, (appt['trabalhador_id'],))

        # Atualiza o agendamento atual
        cur.execute("""
            UPDATE agendamento_exames 
            SET status = %s, observacao = %s, validado_para_psico = %s, atualizado_em = NOW(), atualizado_por = %s
            WHERE id = %s
        """, (final_status, observacao, validado, user_email, id))
        
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
                ae.observacao,
                ae.validado_para_psico,
                ae.funcionario_id,
                ae.atualizado_por
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
    cur = conn.cursor(cursor_factory=RealDictCursor)
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
