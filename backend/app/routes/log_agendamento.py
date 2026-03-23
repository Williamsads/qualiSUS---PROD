from flask import Blueprint, render_template, jsonify, request, session
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import json
from app.database import get_connection

bp_agendamento = Blueprint(
    "log_agendamento",
    __name__,
    url_prefix="/log_agendamento"
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

    # Busca desfecho se houver (Modo Edição/Visualização)
    cur.execute("""
        SELECT dc.*, f.nome as profissional_nome 
        FROM desfechos_clinicos dc
        LEFT JOIN funcionarios f ON dc.criado_por = f.email
        WHERE dc.atendimento_id = %s
    """, (id,))
    desfecho = cur.fetchone()

    cur.close()
    conn.close()
    
    if not appt:
        flash("Agendamento não encontrado.", "erro")
        return redirect(url_for("log_agendamento.index"))
        
    return render_template("atendimento_clinico.html", appt=appt, desfecho=desfecho)

@bp_agendamento.route("/api/atualizar/<int:id>", methods=["POST"])
def api_atualizar(id):
    data = request.json
    status = data.get("status")
    observacao = data.get("observacao")
    desfecho = data.get("desfecho")  # 'nao_compareceu', 'reagendar', 'atendido'
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Busca dados atuais do agendamento + info do paciente para e-mail
        cur.execute("""
            SELECT ae.status, ae.trabalhador_id, ae.vinculo_id, ae.funcionario_id,
                   ae.data_consulta, ae.horario, ae.unidade, ae.especialidade,
                   t.nome_completo as paciente_nome, t.email as paciente_email,
                   f.nome as medico_nome
            FROM agendamento_exames ae
            JOIN trabalhadores t ON ae.trabalhador_id = t.id
            JOIN funcionarios f ON ae.funcionario_id = f.id
            WHERE ae.id = %s
        """, (id,))
        appt = cur.fetchone()
        if not appt:
            return jsonify({"success": False, "error": "Agendamento não encontrado"}), 404

        if "user_id" not in session:
            return jsonify({"success": False, "error": "Acesso negado. Usuário não autenticado no painel."}), 401
            
        # BLOQUEIO DE ALTERAÇÃO: Se já estiver encerrado ou cancelado, não permite editar
        if appt['status'] in ['Finalizado', 'Realizado', 'Cancelado', 'NAO_COMPARECEU']:
            return jsonify({"success": False, "error": "Este atendimento já foi encerrado e não pode mais ser alterado."}), 403

        user_email = session.get("email")
        user_tipo = session.get("tipo", "").upper()
        
        # Busca ID do profissional atual para vincular se for Acolhimento Livre (-1)
        cur.execute("SELECT id FROM funcionarios WHERE email = %s", (user_email,))
        func_row = cur.fetchone()
        real_funcionario_id = func_row['id'] if func_row else None

        # Validação extra de IDOR: Somente o profissional alocado, ou ADMIN/ACOLHIMENTO
        # Como a base tem id `-1` para acolhimento livre, se for ADMIN / ACOLHIMENTO a gente pula a restrição.
        if user_tipo not in ["ADMIN", "GESTOR", "ACOLHIMENTO", "DESENVOLVEDOR"]:
            if appt['funcionario_id'] != -1 and appt['funcionario_id'] != real_funcionario_id:
                 return jsonify({"success": False, "error": "Você não tem permissão para editar um agendamento atribuído a outro médico."}), 403

        
        # --- REGRAS DE NEGÓCIO DE ACOLHIMENTO E DESFECHO ---
        final_status = status
        validado = False

        # 1. TRATAMENTO DE REAGENDAMENTO (COM DATA ESPECÍFICA)
        if desfecho == 'reagendar':
            nova_data    = data.get("nova_data_reagendamento")
            novo_horario = data.get("novo_horario")  # Novo horário escolhido
            motivo       = data.get("motivo", "Não informado")

            if not nova_data:
                nova_data = appt['data_consulta'] + timedelta(days=7)

            # Usa o novo horário se fornecido, caso contrário mantém o original
            horario_final = novo_horario if novo_horario else appt['horario']
            obs_reagendamento = f"Reagendamento do ID {id}. Motivo: {motivo}"

            # Novo profissional?
            novo_func_id = data.get("funcionario_id") or appt['funcionario_id']

            cur.execute("""
                INSERT INTO agendamento_exames
                (trabalhador_id, vinculo_id, funcionario_id, data_consulta, horario, unidade, especialidade, status, observacao, atualizado_por, origem_agendamento)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'Agendado', %s, %s, 'REAGENDAMENTO')
            """, (
                appt['trabalhador_id'], appt['vinculo_id'], novo_func_id,
                nova_data, horario_final, appt['unidade'], appt['especialidade'],
                obs_reagendamento, user_email
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

        # Atualiza o agendamento atual
        # Se o médico original era -1 (Acolhimento Virtual), assume o médico que está salvando agora
        if appt.get('funcionario_id') == -1 and real_funcionario_id:
             cur.execute("""
                UPDATE agendamento_exames 
                SET status = %s, observacao = %s, validado_para_psico = %s, 
                    atualizado_em = NOW(), atualizado_por = %s,
                    funcionario_id = %s
                WHERE id = %s
            """, (final_status, observacao, validado, user_email, real_funcionario_id, id))
        else:
            cur.execute("""
                UPDATE agendamento_exames 
                SET status = %s, observacao = %s, validado_para_psico = %s, atualizado_em = NOW(), atualizado_por = %s
                WHERE id = %s
            """, (final_status, observacao, validado, user_email, id))
        
        conn.commit()

        # --- E-MAIL DE REAGENDAMENTO ---
        if desfecho == 'reagendar' and appt.get('paciente_email'):
            try:
                import os, smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart

                nova_data_fmt = str(nova_data)
                try:
                    from datetime import date as date_type
                    if isinstance(nova_data, str):
                        nova_data_fmt = datetime.strptime(nova_data, '%Y-%m-%d').strftime('%d/%m/%Y')
                    else:
                        nova_data_fmt = nova_data.strftime('%d/%m/%Y')
                except: pass

                horario_fmt = str(horario_final) if horario_final else ''
                try:
                    if hasattr(horario_final, 'strftime'):
                        horario_fmt = horario_final.strftime('%H:%M')
                    elif isinstance(horario_final, str) and len(horario_final) >= 5:
                        horario_fmt = horario_final[:5]
                except: pass

                msg = MIMEMultipart()
                msg['From']    = f"QualiVida PE <{os.getenv('MAIL_DEFAULT_SENDER')}>"
                msg['To']      = appt['paciente_email']
                msg['Subject'] = f"📅 Seu Atendimento foi Reagendado – {appt['especialidade']}"

                html_body = f"""
                <div style="font-family:'Inter','Segoe UI',sans-serif;max-width:600px;margin:0 auto;padding:20px;background:#f8fafc;">
                  <div style="background:#fff;border-radius:16px;padding:40px;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
                    <div style="text-align:center;margin-bottom:24px;">
                      <h2 style="color:#0f172a;margin:0;font-size:22px;font-weight:800;">QualiVida <span style="color:#f59e0b;">PE</span></h2>
                    </div>
                    <div style="background:#fffbeb;color:#92400e;padding:10px 18px;border-radius:999px;font-weight:700;font-size:12px;display:inline-block;margin-bottom:24px;">
                      📅 ATENDIMENTO REAGENDADO
                    </div>
                    <p style="font-size:15px;color:#1e293b;margin-bottom:6px;">Olá, <strong>{appt['paciente_nome']}</strong>,</p>
                    <p style="font-size:13px;color:#64748b;margin-bottom:28px;">Seu atendimento foi reagendado para uma nova data. Confira os detalhes abaixo.</p>
                    <div style="border:1px solid #e2e8f0;border-radius:12px;padding:24px;margin-bottom:20px;">
                      <table width="100%" cellpadding="0" cellspacing="0">
                        <tr><td style="padding:8px 0;border-bottom:1px dashed #e2e8f0;">
                          <span style="font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;">Especialidade</span><br>
                          <span style="font-size:15px;font-weight:800;color:#0f172a;">{appt['especialidade']}</span>
                        </td></tr>
                        <tr><td style="padding:8px 0;border-bottom:1px dashed #e2e8f0;">
                          <span style="font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;">Profissional</span><br>
                          <span style="font-size:14px;font-weight:600;color:#1e293b;">{appt['medico_nome']}</span>
                        </td></tr>
                        <tr><td style="padding:8px 0;border-bottom:1px dashed #e2e8f0;">
                          <span style="font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;">Nova Data e Horário</span><br>
                          <span style="font-size:16px;font-weight:800;color:#f59e0b;">{nova_data_fmt} às {horario_fmt}</span>
                        </td></tr>
                        <tr><td style="padding:8px 0;border-bottom:1px dashed #e2e8f0;">
                          <span style="font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;">Local</span><br>
                          <span style="font-size:14px;font-weight:600;color:#475569;">{appt['unidade']}</span>
                        </td></tr>
                        <tr><td style="padding:8px 0;">
                          <span style="font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;">Motivo do Reagendamento</span><br>
                          <span style="font-size:13px;font-weight:600;color:#64748b;font-style:italic;">{motivo}</span>
                        </td></tr>
                      </table>
                    </div>
                    <div style="background:#f8fafc;border-radius:8px;padding:14px;border:1px solid #f1f5f9;text-align:center;">
                      <p style="margin:0;font-size:12px;color:#64748b;">⚠️ <strong>Lembre-se:</strong> Chegue com 15 minutos de antecedência e porte seu documento original.</p>
                    </div>
                  </div>
                </div>"""

                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
                server = smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT", 587)))
                server.starttls()
                server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
                server.sendmail(os.getenv("MAIL_DEFAULT_SENDER"), appt['paciente_email'], msg.as_string())
                server.quit()
                print(f">>> E-mail de reagendamento enviado para {appt['paciente_email']}")
            except Exception as mail_err:
                print(f"Erro ao enviar e-mail de reagendamento: {mail_err}")

        return jsonify({"success": True})

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@bp_agendamento.route("/api/lista")
def api_lista():
    user_tipo = str(session.get("tipo", "")).upper()
    user_email = session.get("email")
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Busca ID do funcionário logado
        cur.execute("SELECT id FROM funcionarios WHERE email = %s", (user_email,))
        func_row = cur.fetchone()
        funcionario_id_logado = func_row['id'] if func_row else None

        query = """
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
                ae.trabalhador_id,
                ae.funcionario_id,
                ae.atualizado_por,
                dc.conduta,
                dc.cid,
                dc.tipo_desfecho as desfecho_clinico
            FROM agendamento_exames ae
            JOIN trabalhadores t ON ae.trabalhador_id = t.id
            JOIN funcionarios f ON ae.funcionario_id = f.id
            LEFT JOIN vinculos_trabalhadores vt ON ae.vinculo_id = vt.id
            LEFT JOIN desfechos_clinicos dc ON ae.id = dc.atendimento_id
            WHERE 1=1
        """
        params = []

        # REGRA DE VISIBILIDADE:
        # Medico vê: dele OU acolhimento.
        # Admin / Dev vê: tudo.
        if user_tipo == 'MEDICO' and funcionario_id_logado:
            query += " AND (ae.funcionario_id = %s OR ae.especialidade = 'Acolhimento')"
            params.append(funcionario_id_logado)
        elif user_tipo != 'ADMIN' and user_tipo != 'DESENVOLVEDOR' and user_tipo != 'DEV':
            # Outros tipos (se houver) veem apenas o que for deles ou nada por padrão
            query += " AND (ae.funcionario_id = %s)"
            params.append(funcionario_id_logado)

        query += " ORDER BY ae.data_consulta DESC, ae.horario DESC"
        
        cur.execute(query, params)
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
        
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

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

@bp_agendamento.route("/api/datas-disponiveis")
def datas_disponiveis_reagendar():
    funcionario_id = request.args.get("funcionario_id")
    unidade = request.args.get("unidade")
    especialidade_id = request.args.get("especialidade_id")

    if not funcionario_id or not unidade:
        return jsonify([])

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("""
            SELECT DISTINCT d.data::TEXT as data
            FROM generate_series(0, 90) i
            CROSS JOIN LATERAL (SELECT CURRENT_DATE + i AS data) d
            JOIN funcionarios f ON f.id = %s
            JOIN horarios_funcionarios hf ON hf.funcionario_id = f.id
            WHERE hf.dia_semana = CASE WHEN EXTRACT(ISODOW FROM d.data) = 7 THEN 0 ELSE CAST(EXTRACT(ISODOW FROM d.data) AS INTEGER) END
              AND (d.data > CURRENT_DATE OR hf.horario > CURRENT_TIME)
              AND NOT EXISTS (
                  SELECT 1 FROM agendamento_exames ae 
                  WHERE ae.data_consulta = d.data 
                    AND ae.funcionario_id = f.id 
                    AND ae.horario = hf.horario
                    AND ae.status != 'Cancelado'
              )
              AND NOT EXISTS (
                  SELECT 1 FROM bloqueios_agenda ba
                  WHERE ba.data = d.data
                    AND (ba.unidade_id IS NULL OR (SELECT id FROM unidades_saude WHERE nome ILIKE %s LIMIT 1) = ba.unidade_id)
                    AND (ba.funcionario_id IS NULL OR ba.funcionario_id = f.id)
              )
            ORDER BY d.data::TEXT
        """, (funcionario_id, unidade))
        
        datas = [row['data'] for row in cur.fetchall()]
        return jsonify(datas)
    except Exception as e:
        print(f"Erro ao buscar datas reagendar: {e}")
        return jsonify([])
    finally:
        cur.close()
        conn.close()
