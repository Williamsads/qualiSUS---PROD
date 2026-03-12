from flask import Blueprint, render_template, jsonify, request, session
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
<<<<<<< HEAD
import json
from app.database import get_connection
=======
>>>>>>> e1d7adbe17fe5d378b7629e63d43beecc7762f1a

bp_agendamento = Blueprint(
    "log_agendamento",
    __name__,
    url_prefix="/log_agendamento"
)

<<<<<<< HEAD
=======
def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

>>>>>>> e1d7adbe17fe5d378b7629e63d43beecc7762f1a
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

<<<<<<< HEAD
# --- GESTÃO DO CICLO DE CUIDADO (MEUS PACIENTES) ---

@bp_agendamento.route("/meus-pacientes")
def meus_pacientes():
    tipo = str(session.get("tipo", "")).upper()
    if tipo not in ["MEDICO", "ADMIN", "DEV", "DESENVOLVEDOR"]:
        return "Acesso restrito ao perfil clínico, administrativo ou de desenvolvimento.", 403
    return render_template("meus_pacientes.html")

@bp_agendamento.route("/api/ciclo/limpeza-automatica", methods=["POST"])
def api_limpeza_automatica():
    """Concede alta automática após 60 dias de inatividade"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE ciclo_cuidado 
            SET status = 'ENCERRADO_AUTOMATICO', data_alta = NOW()
            WHERE status = 'ATIVO' 
              AND data_ultima_interacao < NOW() - interval '60 days'
        """)
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@bp_agendamento.route("/api/meus-pacientes")
def api_meus_pacientes():
    user_tipo = str(session.get("tipo", "")).upper()
    if user_tipo not in ["MEDICO", "ADMIN", "DEV", "DESENVOLVEDOR"]:
        return jsonify({"error": "Não autorizado"}), 403
        
    user_email = session.get("email")
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Busca o id do funcionário (útil apenas se for médico)
        nome_usuario = session.get("nome")
        cur.execute("SELECT id FROM funcionarios WHERE email = %s", (user_email,))
        funcionario = cur.fetchone()

        if not funcionario and user_email:
            cur.execute("SELECT id FROM funcionarios WHERE LOWER(email) = LOWER(%s)", (user_email,))
            funcionario = cur.fetchone()

        if not funcionario and nome_usuario:
            cur.execute("SELECT id FROM funcionarios WHERE nome = %s", (nome_usuario,))
            funcionario = cur.fetchone()
        
        # SQL Base: Mostra ciclos ATIVOS com info do último atendimento
        query = """
            SELECT 
                cc.id as ciclo_id,
                t.id as trabalhador_id,
                t.nome_completo as paciente,
                TO_CHAR(cc.data_inicio, 'DD/MM/YYYY') as data_inicio,
                TO_CHAR(cc.data_ultima_interacao, 'DD/MM/YYYY') as ultima_interacao,
                cc.status,
                latest_ae.medico_atual,
                latest_ae.especialidade_atual
            FROM ciclo_cuidado cc
            JOIN trabalhadores t ON cc.trabalhador_id = t.id
            LEFT JOIN LATERAL (
                SELECT f.nome as medico_atual, ae.especialidade as especialidade_atual
                FROM agendamento_exames ae
                JOIN funcionarios f ON ae.funcionario_id = f.id
                WHERE ae.trabalhador_id = t.id
                ORDER BY ae.data_consulta DESC, ae.horario DESC
                LIMIT 1
            ) latest_ae ON TRUE
            WHERE cc.status = 'ATIVO'
        """
        params = []

        # REGRA: Se for médico, filtra apenas os dele. Se for ADMIN/DEV, NÃO filtra (vê todos).
        if user_tipo == "MEDICO":
            if funcionario:
                query += """
                  AND EXISTS (
                      SELECT 1 FROM agendamento_exames ae 
                      WHERE ae.trabalhador_id = cc.trabalhador_id 
                        AND ae.funcionario_id = %s
                  )
                """
                params.append(funcionario['id'])
            else:
                # Se é médico mas não identificamos o perfil clínico, não mostra nada por segurança
                query += " AND 1=0"
        
        query += " ORDER BY cc.data_ultima_interacao DESC"
        cur.execute(query, params)
        rows = cur.fetchall()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@bp_agendamento.route("/api/ciclo/alta/<int:ciclo_id>", methods=["POST"])
def api_dar_alta(ciclo_id):
    user_tipo = str(session.get("tipo", "")).upper()
    if user_tipo not in ["MEDICO", "ADMIN", "DEV", "DESENVOLVEDOR"]:
        return jsonify({"success": False, "error": "Apenas médicos, administradores ou desenvolvedores podem dar alta."}), 403
        
    user_email = session.get("email")
    data = request.json
    obs = data.get("observacao", "Alta realizada pelo profissional.")

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Tenta pegar o ID do funcionário se existir (para rastreio de quem deu alta)
        cur.execute("SELECT id FROM funcionarios WHERE email = %s", (user_email,))
        funcionario = cur.fetchone()
        funcionario_id = funcionario['id'] if funcionario else None
        
        cur.execute("""
            UPDATE ciclo_cuidado SET 
                status = 'ALTA', 
                data_alta = NOW(), 
                medico_alta_id = %s,
                data_ultima_interacao = NOW(),
                observacao_alta = %s
            WHERE id = %s AND status = 'ATIVO'
        """, (funcionario_id, obs, ciclo_id))
        
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


@bp_agendamento.route("/atendimento/<int:id>")
def atendimento(id):
    if "user_id" not in session:
        return redirect("/login")
=======
@bp_agendamento.route("/atendimento/<int:id>")
def atendimento(id):
    if "user_id" not in session:
        return redirect("/index")
>>>>>>> e1d7adbe17fe5d378b7629e63d43beecc7762f1a
        
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
<<<<<<< HEAD

    # Busca desfecho se houver (Modo Edição/Visualização)
    cur.execute("""
        SELECT dc.*, f.nome as profissional_nome 
        FROM desfechos_clinicos dc
        LEFT JOIN funcionarios f ON dc.criado_por = f.email
        WHERE dc.atendimento_id = %s
    """, (id,))
    desfecho = cur.fetchone()

=======
>>>>>>> e1d7adbe17fe5d378b7629e63d43beecc7762f1a
    cur.close()
    conn.close()
    
    if not appt:
        flash("Agendamento não encontrado.", "erro")
        return redirect(url_for("log_agendamento.index"))
        
<<<<<<< HEAD
    return render_template("atendimento_clinico.html", appt=appt, desfecho=desfecho)
=======
    return render_template("atendimento_clinico.html", appt=appt)
>>>>>>> e1d7adbe17fe5d378b7629e63d43beecc7762f1a

@bp_agendamento.route("/api/atualizar/<int:id>", methods=["POST"])
def api_atualizar(id):
    data = request.json
    status = data.get("status")
    observacao = data.get("observacao")
    desfecho = data.get("desfecho")  # 'nao_compareceu', 'reagendar', 'atendido'
<<<<<<< HEAD
=======
    apto_psico = data.get("apto_psico") # True/False
>>>>>>> e1d7adbe17fe5d378b7629e63d43beecc7762f1a
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Busca dados atuais do agendamento
        cur.execute("SELECT * FROM agendamento_exames WHERE id = %s", (id,))
        appt = cur.fetchone()
        if not appt:
            return jsonify({"success": False, "error": "Agendamento não encontrado"}), 404

        user_email = session.get("email") or "Sistema"
        
<<<<<<< HEAD
        # --- REGRAS DE NEGÓCIO DE ACOLHIMENTO E DESFECHO ---
        final_status = status
        validado = False

        # 1. TRATAMENTO DE REAGENDAMENTO (COM DATA ESPECÍFICA)
        if desfecho == 'reagendar':
            nova_data = data.get("nova_data_reagendamento")
            if not nova_data:
                # Fallback para +7 dias se não informada
                nova_data = appt['data_consulta'] + timedelta(days=7)
            
            cur.execute("""
                INSERT INTO agendamento_exames 
                (trabalhador_id, vinculo_id, funcionario_id, data_consulta, horario, unidade, especialidade, status, observacao, atualizado_por, origem_agendamento)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'Agendado', %s, %s, 'REAGENDAMENTO')
            """, (
                appt['trabalhador_id'], appt['vinculo_id'], appt['funcionario_id'], 
                nova_data, appt['horario'], appt['unidade'], appt['especialidade'], 
                f"Reagendamento do ID {id}", user_email
            ))

        # 2. TRATAMENTO DE ENCAMINHAMENTO (DURANTE O ATENDIMENTO)
        enc = data.get("encaminhamento")
        if (desfecho == 'atendido' or desfecho == 'encaminhar') and enc:
            # 2.1 Cria o novo agendamento
            cur.execute("""
                INSERT INTO agendamento_exames 
                (trabalhador_id, vinculo_id, funcionario_id, data_consulta, horario, unidade, especialidade, status, observacao, atualizado_por, origem_agendamento)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'Agendado', %s, %s, 'ENCAMINHAMENTO')
            """, (
                appt['trabalhador_id'], appt['vinculo_id'], enc.get("profissional_id"), 
                enc.get("data"), enc.get("horario"), appt['unidade'], enc.get("especialidade"), 
                f"Encaminhamento gerado no atendimento ID {id}", user_email
            ))

            # 2.2 Garante ciclo ativo e vínculo clínico (Fase de Tratamento)
            cur.execute("""
                INSERT INTO ciclo_cuidado (trabalhador_id, status, data_inicio, data_ultima_interacao)
                VALUES (%s, 'ATIVO', NOW(), NOW())
                ON CONFLICT (trabalhador_id) DO UPDATE 
                SET status = 'ATIVO', data_ultima_interacao = NOW(), data_alta = NULL
                RETURNING id
            """, (appt['trabalhador_id'],))
            ciclo_id = cur.fetchone()['id']

            cur.execute("""
                INSERT INTO paciente_tratamento (trabalhador_id, ciclo_id, medico_id, status, criado_em, criado_por)
                VALUES (%s, %s, %s, 'EM_TRATAMENTO', NOW(), %s)
                ON CONFLICT (ciclo_id, trabalhador_id) DO UPDATE 
                SET status = 'EM_TRATAMENTO', medico_id = %s, atualizado_em = NOW(), atualizado_por = %s
            """, (appt['trabalhador_id'], ciclo_id, enc.get("profissional_id"), user_email, enc.get("profissional_id"), user_email))

        # 3. REGRAS ESPECÍFICAS DE ACOLHIMENTO
        if appt['especialidade'] == 'Acolhimento' and desfecho:
            if desfecho == 'nao_compareceu':
                final_status = 'NAO_COMPARECEU'
            elif desfecho in ['atendido', 'encaminhar', 'alta_medica', 'alta_adm']:
                final_status = 'Finalizado'
                if enc: validado = True
                
                # Atualiza interação do ciclo (caso não tenha entrado no IF do enc acima)
                cur.execute("""
                    UPDATE ciclo_cuidado SET data_ultima_interacao = NOW() 
                    WHERE trabalhador_id = %s AND status = 'ATIVO'
                """, (appt['trabalhador_id'],))

        # 4. SALVAR NA TABELA desfechos_clinicos (ENTERPRISE)
        conduta = data.get("conduta")
        cid = data.get("cid")
        metadata = json.dumps(data.get("encaminhamento"), default=str) if data.get("encaminhamento") else None
        
        # Busca se já existe desfecho para este atendimento
        cur.execute("SELECT * FROM desfechos_clinicos WHERE atendimento_id = %s", (id,))
        desfecho_existente = cur.fetchone()
        
        if desfecho_existente:
            # Update and Log
            cur.execute("""
                UPDATE desfechos_clinicos 
                SET tipo_desfecho = %s, conduta = %s, observacoes = %s, cid = %s, 
                    atualizado_por = %s, atualizado_em = NOW(), status = 'Ativo', metadata = %s
                WHERE atendimento_id = %s
            """, (desfecho, conduta, observacao, cid, user_email, metadata, id))
            
            cur.execute("""
                INSERT INTO desfecho_logs (desfecho_id, usuario_id, acao, antes, depois)
                VALUES (%s, %s, 'UPDATE', %s, %s)
            """, (desfecho_existente['id'], user_email, json.dumps(desfecho_existente, default=str), json.dumps(data, default=str)))
        else:
            # Insert and Log
            cur.execute("""
                INSERT INTO desfechos_clinicos 
                (paciente_id, atendimento_id, tipo_desfecho, conduta, observacoes, cid, criado_por, atualizado_por, status, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Ativo', %s)
                RETURNING id
            """, (appt['trabalhador_id'], id, desfecho, conduta, observacao, cid, user_email, user_email, metadata))
            new_id_data = cur.fetchone()
            new_desfecho_id = new_id_data['id']
            
            cur.execute("""
                INSERT INTO desfecho_logs (desfecho_id, usuario_id, acao, antes, depois)
                VALUES (%s, %s, 'CREATE', NULL, %s)
            """, (new_desfecho_id, user_email, json.dumps(data, default=str)))
=======
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
>>>>>>> e1d7adbe17fe5d378b7629e63d43beecc7762f1a

        # Atualiza o agendamento atual
        cur.execute("""
            UPDATE agendamento_exames 
            SET status = %s, observacao = %s, validado_para_psico = %s, atualizado_em = NOW(), atualizado_por = %s
            WHERE id = %s
        """, (final_status, observacao, validado, user_email, id))
        
        conn.commit()
        return jsonify({"success": True})
<<<<<<< HEAD

=======
>>>>>>> e1d7adbe17fe5d378b7629e63d43beecc7762f1a
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
<<<<<<< HEAD
                ae.trabalhador_id,
                ae.funcionario_id,
                ae.atualizado_por,
                dc.conduta,
                dc.cid,
                dc.tipo_desfecho as desfecho_clinico
=======
                ae.funcionario_id,
                ae.atualizado_por
>>>>>>> e1d7adbe17fe5d378b7629e63d43beecc7762f1a
            FROM agendamento_exames ae
            JOIN trabalhadores t ON ae.trabalhador_id = t.id
            JOIN funcionarios f ON ae.funcionario_id = f.id
            LEFT JOIN vinculos_trabalhadores vt ON ae.vinculo_id = vt.id
<<<<<<< HEAD
            LEFT JOIN desfechos_clinicos dc ON ae.id = dc.atendimento_id
=======
>>>>>>> e1d7adbe17fe5d378b7629e63d43beecc7762f1a
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
<<<<<<< HEAD
        # Busca ID do desfecho para limpar logs primeiro
        cur.execute("SELECT id FROM desfechos_clinicos WHERE atendimento_id = %s", (id,))
        desfecho = cur.fetchone()
        
        if desfecho:
            # Deleta logs vinculados ao desfecho
            cur.execute("DELETE FROM desfecho_logs WHERE desfecho_id = %s", (desfecho['id'],))
            # Deleta o desfecho clínico
            cur.execute("DELETE FROM desfechos_clinicos WHERE id = %s", (desfecho['id'],))

        # Deleta o agendamento
        cur.execute("DELETE FROM agendamento_exames WHERE id = %s", (id,))
        
=======
        cur.execute("DELETE FROM agendamento_exames WHERE id = %s", (id,))
>>>>>>> e1d7adbe17fe5d378b7629e63d43beecc7762f1a
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()
<<<<<<< HEAD

@bp_agendamento.route("/api/cancelar/<int:id>", methods=["POST"])
def api_cancelar(id):
    user_email = session.get("email") or "Sistema/Admin"
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            UPDATE agendamento_exames 
            SET status = 'Cancelado', 
                atualizado_em = NOW(),
                atualizado_por = %s
            WHERE id = %s
        """, (user_email, id))
        
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

=======
>>>>>>> e1d7adbe17fe5d378b7629e63d43beecc7762f1a
