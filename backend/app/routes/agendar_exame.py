from flask import Flask, Blueprint, request, jsonify, render_template,session
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timedelta

# ----------------------
# CONFIGURAÇÃO DO FLASK
# ----------------------
app = Flask(__name__, template_folder="templates", static_folder="static")

# ----------------------
# BLUEPRINT AGENDAMENTO
# ----------------------
agendamento_bp = Blueprint("agendamento_bp", __name__, template_folder="templates")


# ----------------------
# CONEXÃO COM O BANCO
# ----------------------
def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

# ----------------------
# ROTA PRINCIPAL (HTML)
# ----------------------
@agendamento_bp.route("/agendar_exame/")
def pagina_agendamento():
    return render_template("agendar_exame.html")


# ====================
# VALIDAR TRABALHADOR
# ====================
@agendamento_bp.route("/api/agendar_exame/trabalhador/validar")
def validar_trabalhador():
    doc = request.args.get("doc", "").strip()
    # Limpa apenas para o CPF (que no banco geralmente é numérico)
    doc_limpo = "".join(filter(str.isdigit, doc))
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Busca abrangente: CPF exato, Vínculo exato ou Vínculo parcial (com ou sem barra)
    cur.execute("""
        SELECT
            t.id,
            t.nome_completo,
            t.cpf,
            t.cns,
            t.data_nascimento,
            t.telefone,
            t.email,
            t.acolhimento_realizado,
            vt.id AS vinculo_id,
            vt.numero_funcional,
            vt.tipo_vinculo,
            vt.especialidade,
            vt.unidade_lotacao,
            vt.data_admissao,
            vt.data_desligamento
        FROM trabalhadores t
        LEFT JOIN vinculos_trabalhadores vt
            ON vt.trabalhador_id = t.id
        WHERE t.cpf = %s 
           OR vt.numero_funcional = %s
           OR vt.numero_funcional LIKE %s
           OR REPLACE(vt.numero_funcional, '/', '') LIKE %s
        ORDER BY CASE WHEN vt.numero_funcional = %s THEN 0 ELSE 1 END
        LIMIT 1
    """, (doc_limpo, doc, f"%{doc}%", f"%{doc_limpo}%", doc))

    resultado = cur.fetchone()

    if not resultado:
        cur.close()
        conn.close()
        return jsonify({"found": False})

    # Busca todas as unidades onde o trabalhador está lotado
    cur.execute("""
        SELECT DISTINCT unidade_lotacao 
        FROM vinculos_trabalhadores 
        WHERE trabalhador_id = %s AND unidade_lotacao IS NOT NULL
        ORDER BY unidade_lotacao
    """, (resultado["id"],))
    unidades_lotadas = [row["unidade_lotacao"] for row in cur.fetchall()]

    cur.close()
    conn.close()

    # 🔐 salva na sessão
    session["trabalhador_id"] = resultado["id"]

    cadastro_incompleto = (
        not resultado["cns"]
        or not resultado["data_nascimento"]
        or not resultado["telefone"]
    )

    proxima_etapa = not cadastro_incompleto

    return jsonify({
        "found": True,
        "trabalhador": resultado,
        "unidades_lotadas": unidades_lotadas,
        "proxima_etapa": proxima_etapa
    })



@agendamento_bp.route("/api/agendar_exame/trabalhador/by-id")
def get_trabalhador_by_id():
    tid = request.args.get("id")
    if not tid:
        return jsonify({"found": False}), 400
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT t.*, vt.id AS vinculo_id, vt.numero_funcional 
            FROM trabalhadores t 
            LEFT JOIN vinculos_trabalhadores vt ON vt.trabalhador_id = t.id 
            WHERE t.id = %s LIMIT 1
        """, (tid,))
        resultado = cur.fetchone()
        
        if not resultado:
            return jsonify({"found": False})

        # Busca todas as unidades
        cur.execute("SELECT DISTINCT unidade_lotacao FROM vinculos_trabalhadores WHERE trabalhador_id = %s", (tid,))
        unidades_lotadas = [row["unidade_lotacao"] for row in cur.fetchall()]

        session["trabalhador_id"] = resultado["id"]
        
        cadastro_incompleto = (not resultado["cns"] or not resultado["data_nascimento"] or not resultado["telefone"])
        return jsonify({
            "found": True,
            "trabalhador": resultado,
            "unidades_lotadas": unidades_lotadas,
            "proxima_etapa": not cadastro_incompleto
        })
    finally:
        cur.close()
        conn.close()

@agendamento_bp.route("/api/agendar_exame/trabalhador/atualizar-completo", methods=["POST", "PUT"])
def atualizar_cadastro():
    data = request.json
    trabalhador = data.get("trabalhador", {})
    vinculo = data.get("vinculo", {})

    trabalhador_id = session.get("trabalhador_id")
    if not trabalhador_id:
        return jsonify({
            "success": False,
            "error": "Sessão expirada. Valide o trabalhador novamente."
        }), 401
    
    # Sanitização Helper
    def clean(val):
        if isinstance(val, str):
            val = val.strip()
            if val == "":
                return None
        return val

    # Sanitiza CEP especificamente
    def clean_cep(val):
        if not val: return None
        # Remove tudo que não é dígito
        import re
        val = re.sub(r'\D', '', str(val))
        return val[:8] if val else None

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Prepara dados sanitizados
        t_nome = clean(trabalhador.get("nome_completo"))
        t_cns = clean(trabalhador.get("cns"))
        t_nasc = clean(trabalhador.get("data_nascimento"))
        t_tel = clean(trabalhador.get("telefone"))
        t_email = clean(trabalhador.get("email"))
        t_cep = clean_cep(trabalhador.get("cep"))
        t_log = clean(trabalhador.get("logradouro"))
        t_num = clean(trabalhador.get("numero"))
        t_bairro = clean(trabalhador.get("bairro"))
        t_cid = clean(trabalhador.get("cidade"))
        t_uf = clean(trabalhador.get("uf"))

        v_num_func = clean(vinculo.get("numero_funcional"))
        v_tipo = clean(vinculo.get("tipo_vinculo"))
        v_esp = clean(vinculo.get("especialidade"))
        v_uni = clean(vinculo.get("unidade_lotacao"))
        v_adm = clean(vinculo.get("data_admissao"))
        v_des = clean(vinculo.get("data_desligamento"))


        # 🔹 TRABALHADOR
        cur.execute("""
            UPDATE trabalhadores SET
              nome_completo = COALESCE(%s, nome_completo),
              cns = COALESCE(%s, cns),
              data_nascimento = COALESCE(%s, data_nascimento),
              telefone = COALESCE(%s, telefone),
              email = COALESCE(%s, email),
              cep = COALESCE(%s, cep),
              logradouro = COALESCE(%s, logradouro),
              numero = COALESCE(%s, numero),
              bairro = COALESCE(%s, bairro),
              cidade = COALESCE(%s, cidade),
              uf = COALESCE(%s, uf)
            WHERE id = %s
        """, (
            t_nome, t_cns, t_nasc, t_tel, t_email, t_cep, 
            t_log, t_num, t_bairro, t_cid, t_uf,
            trabalhador_id
        ))

        # 🔹 VÍNCULO
        cur.execute("""
            UPDATE vinculos_trabalhadores SET
              numero_funcional = COALESCE(%s, numero_funcional),
              tipo_vinculo = COALESCE(%s, tipo_vinculo),
              especialidade = COALESCE(%s, especialidade),
              unidade_lotacao = COALESCE(%s, unidade_lotacao),
              data_admissao = COALESCE(%s, data_admissao),
              data_desligamento = COALESCE(%s, data_desligamento)
            WHERE trabalhador_id = %s
        """, (
            v_num_func, v_tipo, v_esp, v_uni, v_adm, v_des,
            trabalhador_id
        ))

        conn.commit()

    except Exception as e:
        conn.rollback()
        return jsonify({
            "success": False,
            "error": "Erro ao atualizar cadastro (DB)",
            "details": str(e)
        }), 500

    finally:
        cur.close()
        conn.close()

    return jsonify({
        "success": True,
        "message": "Cadastro atualizado com sucesso"
    })


# ====================
# Unidade / data disponível
# ====================
@agendamento_bp.route("/api/agendar_exame/unidades_disponiveis")
def unidades_disponiveis():
    especialidade_id = request.args.get("especialidade_id")
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    if especialidade_id:
        cur.execute("""
            SELECT DISTINCT u.id, u.nome, u.endereco 
            FROM unidades_saude u
            JOIN unidades_especialidades ue ON ue.unidade_id = u.id
            WHERE ue.especialidade_id = %s
            ORDER BY u.nome
        """, (especialidade_id,))
    else:
        cur.execute("SELECT id, nome, endereco FROM unidades_saude ORDER BY nome")
        
    unidades = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify({"unidades": unidades})

# ====================
# Especialidades disponíveis
# ====================
@agendamento_bp.route("/api/agendar_exame/especialidades")
def especialidades_disponiveis():
    unidade_id = request.args.get("unidade_id")
    include_hidden = request.args.get("include_hidden", "false").lower() == "true"
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    visivel_filter = "AND e.visivel = true" if not include_hidden else ""
    visivel_filter_no_alias = "WHERE visivel = true" if not include_hidden else ""

    if unidade_id:
        cur.execute(f"""
            SELECT e.id, e.nome, e.icone, e.tipo_fluxo, e.exige_acolhimento_previo 
            FROM especialidades e
            JOIN unidades_especialidades ue ON ue.especialidade_id = e.id
            WHERE ue.unidade_id = %s {visivel_filter}
            ORDER BY e.nome
        """, (unidade_id,))
    else:
        # Corrigido: Se não for para incluir ocultos, usa WHERE (ou 1=1 se for para incluir)
        query = f"SELECT id, nome, icone, tipo_fluxo, exige_acolhimento_previo FROM especialidades {visivel_filter_no_alias} ORDER BY nome"
        cur.execute(query)
        
    especialidades = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify({"especialidades": especialidades})

# ====================
# VALIDAR ACOLHIMENTO (Regra de Negócio)
# ====================
@agendamento_bp.route("/api/agendar_exame/check-acolhimento")
def check_acolhimento():
    trabalhador_id = request.args.get("trabalhador_id")
    especialidade_nome = request.args.get("especialidade")

    user_tipo = str(session.get("tipo", "")).upper()
    perfil_paciente = ["TRABALHADOR", "USUARIO", "PACIENTE", ""]

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 1. Busca regra da especialidade (Case Insensitive)
        cur.execute("SELECT id, nome, exige_acolhimento_previo FROM especialidades WHERE LOWER(nome) = LOWER(%s)", (especialidade_nome,))
        spec = cur.fetchone()

        if not spec:
            return jsonify({"blocked": False})

        # 2. Se exige acolhimento, verifica a flag no perfil do trabalhador
        if spec['exige_acolhimento_previo']:
            # Se for profissional, libera sempre
            if user_tipo not in perfil_paciente:
                return jsonify({"blocked": False})

            # Se for paciente, verifica a flag no banco
            cur.execute("SELECT acolhimento_realizado FROM trabalhadores WHERE id = %s", (trabalhador_id,))
            t_data = cur.fetchone()
            
            flag_realizado = t_data['acolhimento_realizado'] if t_data else False

            if not flag_realizado:
                msg = "Para agendar esta especialidade, é necessário realizar o Acolhimento Social primeiro."
                return jsonify({
                    "blocked": True,
                    "reason": "necessita_acolhimento",
                    "message": msg
                })

        return jsonify({"blocked": False})
    except Exception as e:
        return jsonify({"blocked": False, "error": str(e)}) # Em caso de erro, libera para não travar o fluxo
    finally:
        cur.close()
        conn.close()

# ====================
# Profissionais por especialidade
# ====================
@agendamento_bp.route("/api/agendar_exame/profissionais")
def profissionais_por_especialidade():
    especialidade_id = request.args.get("especialidade_id")
    unidade_atendimento = request.args.get("unidade") 
    
    if not especialidade_id:
        return jsonify({"profissionais": []})

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    query = """
        SELECT f.id, f.nome, f.especialidade, f.unidade_atendimento 
        FROM funcionarios f
        JOIN funcionarios_especialidades fe ON fe.funcionario_id = f.id
        WHERE fe.especialidade_id = %s 
          AND f.ativo = TRUE 
          AND f.atendimento = TRUE 
          AND COALESCE(f.situacao, 'Ativo') = 'Ativo'
    """
    params = [especialidade_id]
    
    if unidade_atendimento:
        query += " AND f.unidade_atendimento ILIKE %s"
        params.append(unidade_atendimento)
        
    cur.execute(query, params)
    profissionais = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify({"profissionais": profissionais})

# ====================
# Horários Disponíveis por Profissional e Data
# ====================
@agendamento_bp.route("/api/agendar_exame/horarios")
def horarios_disponiveis():
    medico_id = request.args.get("medico_id")
    data_str = request.args.get("data")
    
    if not medico_id or not data_str:
        return jsonify([])

    try:
        data_obj = datetime.strptime(data_str, '%Y-%m-%d')
        dia_semana = data_obj.weekday() + 1 # weekday() é 0=Segunda, +1 vira 1=Segunda, ..., 7=Domingo
        # Atenção: No JS getDay() é 0=Domingo. No Python weekday() é 0=Segunda.
        # Vamos padronizar com o que está no banco. 
        # Geralmente horarios_funcionarios usa 0=Domingo ou 1=Segunda.
        # Vou assumir que o sistema de gerenciamento usa 0=Domingo a 6=Sábado (padrão JS).
        dia_semana_oficial = data_obj.isoweekday() # 1=Segunda, ..., 7=Domingo
        if dia_semana_oficial == 7: dia_semana_oficial = 0 # Converte Domingo de 7 para 0
    except:
        return jsonify([])

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 1. Busca horários base do profissional para aquele dia da semana
    cur.execute("""
        SELECT TO_CHAR(horario, 'HH24:MI') as horario 
        FROM horarios_funcionarios 
        WHERE funcionario_id = %s AND dia_semana = %s
        ORDER BY horario
    """, (medico_id, dia_semana_oficial))
    
    todos_horarios = cur.fetchall()
    
    # 2. Busca horários já ocupados
    cur.execute("""
        SELECT TO_CHAR(horario, 'HH24:MI') as horario 
        FROM agendamento_exames 
        WHERE funcionario_id = %s AND data_consulta = %s AND status != 'Cancelado'
    """, (medico_id, data_str))
    
    ocupados = [row['horario'] for row in cur.fetchall()]
    
    # 3. Filtra
    disponiveis = [h for h in todos_horarios if h['horario'] not in ocupados]
    
    cur.close()
    conn.close()
    return jsonify(disponiveis)

# ====================
# Dias da Semana Disponíveis por Profissional
# ====================
@agendamento_bp.route("/api/agendar_exame/datas_disponiveis")
def dias_disponiveis_profissional():
    medico_id = request.args.get("medico_id")
    if not medico_id:
        return jsonify([])

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT DISTINCT dia_semana 
        FROM horarios_funcionarios 
        WHERE funcionario_id = %s
    """, (medico_id,))
    
    dias = [row['dia_semana'] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(dias)

# ====================
# Confirmar Agendamento
# ====================
@agendamento_bp.route("/api/agendar_exame/confirmar", methods=["POST"])
def confirmar_agendamento():
    data = request.json
    
    trabalhador_id = session.get("trabalhador_id")
    if not trabalhador_id:
        return jsonify({"success": False, "error": "Sessão expirada. Valide o trabalhador novamente."}), 401

    vinculo_id = data.get("vinculo_id")
    funcionario_id = data.get("funcionario_id") # Este é o ID do Profissional
    data_consulta = data.get("data_consulta")
    horario = data.get("horario")
    unidade = data.get("unidade")
    especialidade = data.get("especialidade")

    # --- [A] IDENTIFICAÇÃO DO PERFIL ---
    user_tipo = str(session.get("tipo", "")).upper()
    user_email = session.get("email")
    perfil_paciente = ["TRABALHADOR", "USUARIO", "PACIENTE"] 
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # --- [B] BUSCAR REGRAS DA ESPECIALIDADE (Case Insensitive) ---
        cur.execute("SELECT id, nome, exige_acolhimento_previo, tipo_fluxo FROM especialidades WHERE LOWER(nome) = LOWER(%s) LIMIT 1", (especialidade,))
        spec = cur.fetchone()
        
        if not spec:
            return jsonify({"success": False, "error": "Especialidade inválida."}), 404
            
        especialidade_id = spec['id']
        exige_acolhimento = spec['exige_acolhimento_previo']
        tipo_fluxo = spec['tipo_fluxo']

        # --- [C] VALIDAÇÃO DO GATE DE ACOLHIMENTO ---
        if exige_acolhimento:
            # Verifica se o paciente já foi liberado
            cur.execute("SELECT acolhimento_realizado FROM trabalhadores WHERE id = %s", (trabalhador_id,))
            t_data = cur.fetchone()
            
            flag_realizado = t_data['acolhimento_realizado'] if t_data else False
            
            # Se não fez acolhimento, pacientes são bloqueados. 
            if not flag_realizado and (user_tipo in perfil_paciente):
                return jsonify({
                    "success": False, 
                    "error": "Para agendar esta especialidade, é necessário realizar o Acolhimento primeiro."
                }), 403

        # --- [D] DEFINIÇÃO DE ORIGEM ---
        if tipo_fluxo == 'ACOLHIMENTO':
            origem = "AUTOAGENDAMENTO"
        else:
            origem = "REGULACAO" if user_tipo not in perfil_paciente else "AUTOAGENDAMENTO"

        # --- VALIDAÇÕES DE DATA/HORA E DUPLICIDADE (MANTIDAS) ---
        try:
            agendamento_datetime = datetime.strptime(f"{data_consulta} {horario}", '%Y-%m-%d %H:%M')
            agora = datetime.now()
            if agendamento_datetime < agora:
                return jsonify({"success": False, "error": "Horário inválido (passado)."}), 400
            if agendamento_datetime.year != agora.year or agendamento_datetime.month != agora.month:
                return jsonify({"success": False, "error": "Agendamentos limitados ao mês atual."}), 400
        except ValueError:
            return jsonify({"success": False, "error": "Formato de data inválido."}), 400

        cur.execute("SELECT id FROM agendamento_exames WHERE trabalhador_id = %s AND data_consulta = %s AND horario = %s AND status != 'Cancelado'", (trabalhador_id, data_consulta, horario))
        if cur.fetchone():
            return jsonify({"success": False, "error": "Já existe agendamento neste horário para o paciente."}), 400

        cur.execute("SELECT id FROM agendamento_exames WHERE funcionario_id = %s AND data_consulta = %s AND horario = %s AND status != 'Cancelado'", (funcionario_id, data_consulta, horario))
        if cur.fetchone():
            return jsonify({"success": False, "error": "Agenda do profissional ocupada."}), 400

        # --- INSERÇÃO COM AUDITORIA COMPLETA ---
        cur.execute("""
            INSERT INTO agendamento_exames (
                trabalhador_id, vinculo_id, funcionario_id, 
                data_consulta, horario, unidade, especialidade, status,
                criado_por, perfil_criador, origem_agendamento, criado_em
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'Agendado', %s, %s, %s, NOW())
        """, (
            trabalhador_id, vinculo_id, funcionario_id,
            data_consulta, horario, unidade, especialidade,
            user_email, user_tipo, origem
        ))

        # --- VÍNCULO AUTOMÁTICO NA GESTÃO DE PACIENTES ---
        # Se for uma consulta especializada (não acolhimento) e o paciente estiver sem responsável, já vincula ao médico agendado.
        especialidade_normalizada = str(especialidade).lower()
        if "acolhimento" not in especialidade_normalizada:
            cur.execute("""
                UPDATE paciente_tratamento SET 
                    medico_id = %s, 
                    atualizado_em = NOW(), 
                    atualizado_por = %s
                WHERE trabalhador_id = %s 
                  AND status = 'EM_TRATAMENTO' 
                  AND medico_id IS NULL
            """, (funcionario_id, user_email, trabalhador_id))

        conn.commit()
        return jsonify({"success": True, "message": "Agendamento realizado com sucesso."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


# ====================
# Listar Agendamentos do Trabalhador
# ====================
@agendamento_bp.route("/api/agendar_exame/trabalhador/agendamentos")
def agendamentos_por_trabalhador():
    trabalhador_id = request.args.get("trabalhador_id") or session.get("trabalhador_id")
    
    if not trabalhador_id:
        return jsonify({"agendamentos": []})

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT 
                ae.id,
                ae.status,
                ae.especialidade,
                f.nome as medico,
                TO_CHAR(ae.data_consulta, 'YYYY-MM-DD') as data,
                TO_CHAR(ae.horario, 'HH24:MI') as horario,
                ae.unidade
            FROM agendamento_exames ae
            JOIN funcionarios f ON ae.funcionario_id = f.id
            WHERE ae.trabalhador_id = %s AND ae.status = 'Agendado'
            ORDER BY ae.data_consulta DESC, ae.horario DESC
        """, (trabalhador_id,))
        rows = cur.fetchall()
        return jsonify({"agendamentos": rows})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

# ====================
# Cancelar Agendamento
# ====================
@agendamento_bp.route("/api/agendar_exame/cancelar", methods=["POST"])
def cancelar_agendamento():
    data = request.json
    agendamento_id = data.get("agendamento_id")
    
    if not agendamento_id:
        return jsonify({"success": False, "error": "ID do agendamento não informado."}), 400

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Busca detalhes do agendamento para validar prazo
        cur.execute("""
            SELECT data_consulta, horario 
            FROM agendamento_exames 
            WHERE id = %s
        """, (agendamento_id,))
        agendamento = cur.fetchone()
        
        if not agendamento:
            return jsonify({"success": False, "error": "Agendamento não encontrado."}), 404
            
        # Combina data e hora
        consulta_datetime = datetime.combine(agendamento['data_consulta'], agendamento['horario'])
        agora = datetime.now()
        
        if (consulta_datetime - agora) < timedelta(hours=12):
            return jsonify({
                "success": False, 
                "error": "O cancelamento só é permitido com pelo menos 12 horas de antecedência."
            }), 403
            
        cur.execute("UPDATE agendamento_exames SET status = 'Cancelado' WHERE id = %s", (agendamento_id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()



# ====================
# REGISTRAR BLUEPRINT
# ====================
app.register_blueprint(agendamento_bp)

# ====================
# RODAR SERVIDOR
# ====================
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
