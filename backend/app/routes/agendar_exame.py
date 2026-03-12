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



# ====================
# ATUALIZAR TRABALHADOR + VÍNCULO
# ====================
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
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, nome, endereco FROM unidades_saude")
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
            SELECT e.id, e.nome, e.icone 
            FROM especialidades e
            JOIN unidades_especialidades ue ON ue.especialidade_id = e.id
            WHERE ue.unidade_id = %s {visivel_filter}
            ORDER BY e.nome
        """, (unidade_id,))
    else:
        # Corrigido: Se não for para incluir ocultos, usa WHERE (ou 1=1 se for para incluir)
        query = f"SELECT id, nome, icone FROM especialidades {visivel_filter_no_alias} ORDER BY nome"
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
    especialidade = request.args.get("especialidade", "")
    
    if not trabalhador_id or especialidade not in ["Psicólogo", "Psiquiatra"]:
        return jsonify({"blocked": False})

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Regra: Bloqueia se NÃO houver um acolhimento 'Validado'
        cur.execute("""
            SELECT id, status, validado_para_psico FROM agendamento_exames 
            WHERE trabalhador_id = %s 
              AND especialidade = 'Acolhimento'
              AND status != 'Cancelado'
            ORDER BY data_consulta DESC, horario DESC
            LIMIT 1
        """, (trabalhador_id,))
        
        acolhimento = cur.fetchone()
        
        if not acolhimento:
            return jsonify({
                "blocked": True, 
                "reason": "missing",
                "message": "Antes do atendimento em Psicologia ou Psiquiatria, é necessário passar pelo Acolhimento Presencial e ser validado pelo profissional."
            })
            
        if not acolhimento['validado_para_psico']:
            if acolhimento['status'] == 'Finalizado':
                return jsonify({
                    "blocked": True, 
                    "reason": "not_eligible",
                    "message": "Seu acolhimento foi finalizado, mas o profissional indicou que você ainda não está apto para seguir para Psicologia/Psiquiatria neste momento."
                })
            else:
                return jsonify({
                    "blocked": True, 
                    "reason": "pending",
                    "message": "Seu acolhimento ainda não foi realizado ou validado pelo profissional responsável."
                })
            
        return jsonify({"blocked": False})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
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

    if not all([data_consulta, horario, funcionario_id]):
        return jsonify({"success": False, "error": "Dados incompletos para o agendamento."}), 400

    conn = get_connection()
    cur = conn.cursor()

    try:
        # --- REGRA DE NEGÓCIO: Acolhimento obrigatório e validado para Psicologia/Psiquiatria ---
        if especialidade in ["Psicólogo", "Psiquiatra"]:
            cur.execute("""
                SELECT validado_para_psico FROM agendamento_exames 
                WHERE trabalhador_id = %s AND especialidade = 'Acolhimento' AND status != 'Cancelado'
                ORDER BY data_consulta DESC, horario DESC LIMIT 1
            """, (trabalhador_id,))
            acolhimento = cur.fetchone()
            if not acolhimento or not acolhimento[0]:
                return jsonify({
                    "success": False, 
                    "error": "Acolhimento obrigatório não realizado ou não autorizado pelo profissional."
                }), 403

        # --- VALIDAÇÃO DE DATA E HORA ---
        try:
            # Combina data e hora para validação completa
            agendamento_datetime = datetime.strptime(f"{data_consulta} {horario}", '%Y-%m-%d %H:%M')
            agora = datetime.now()

            # 1. Bloqueio de passado: não permitir retroativos
            if agendamento_datetime < agora:
                return jsonify({
                    "success": False, 
                    "error": "Não é possível realizar agendamentos para datas ou horários que já passaram."
                }), 400

            # 2. Bloqueio mensal: Validar se a data é do mês atual
            if agendamento_datetime.year != agora.year or agendamento_datetime.month != agora.month:
                return jsonify({
                    "success": False, 
                    "error": "Agendamentos só podem ser realizados para datas dentro do mês atual."
                }), 400

        except ValueError:
            return jsonify({"success": False, "error": "Formato de data ou hora inválido."}), 400

        # Verificar duplicidade para o paciente (mesmo horário)
        cur.execute("""
            SELECT id FROM agendamento_exames 
            WHERE trabalhador_id = %s 
              AND data_consulta = %s 
              AND horario = %s 
              AND status != 'Cancelado'
        """, (trabalhador_id, data_consulta, horario))
        if cur.fetchone():
            return jsonify({"success": False, "error": "Você já possui um agendamento neste horário."}), 400

        # Verificar duplicidade para o médico (mesmo horário) - Evita conflito de agenda
        cur.execute("""
            SELECT id FROM agendamento_exames 
            WHERE funcionario_id = %s 
              AND data_consulta = %s 
              AND horario = %s 
              AND status != 'Cancelado'
        """, (funcionario_id, data_consulta, horario))
        if cur.fetchone():
            return jsonify({"success": False, "error": "Este horário já foi preenchido por outro paciente."}), 400

        cur.execute("""
            INSERT INTO agendamento_exames (
                trabalhador_id, vinculo_id, funcionario_id, 
                data_consulta, horario, unidade, especialidade, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'Agendado')
        """, (
            trabalhador_id, vinculo_id, funcionario_id,
            data_consulta, horario, unidade, especialidade
        ))
        conn.commit()
        return jsonify({"success": True})
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
            WHERE ae.trabalhador_id = %s AND ae.status != 'Cancelado'
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
        
        if (consulta_datetime - agora) < timedelta(hours=24):
            return jsonify({
                "success": False, 
                "error": "O cancelamento só é permitido com pelo menos 24 horas de antecedência."
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
    app.run(debug=False, host="0.0.0.0", port=5000)
