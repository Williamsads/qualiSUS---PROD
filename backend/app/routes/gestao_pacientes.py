from flask import Blueprint, render_template, jsonify, request, session
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from app.database import get_connection

gestao_pacientes_bp = Blueprint(
    "gestao_pacientes",
    __name__,
    url_prefix="/gestao-pacientes"
)


def _require_medico():
    """Verifica se o usuário logado é médico (ou admin/dev). Retorna (ok, funcionario_id, user_tipo)."""
    tipo = str(session.get("tipo", "")).upper()
    if tipo not in ["MEDICO", "ADMIN", "DESENVOLVEDOR", "DEV"]:
        return False, None, tipo

    email = session.get("email")
    nome = session.get("nome")
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 1. Tenta por e-mail exato
    cur.execute("SELECT id FROM funcionarios WHERE email = %s", (email,))
    func = cur.fetchone()

    # 2. Tenta por e-mail case-insensitive
    if not func and email:
        cur.execute("SELECT id FROM funcionarios WHERE LOWER(email) = LOWER(%s)", (email,))
        func = cur.fetchone()

    # 3. Tenta por Nome (Se for Médico, ajuda em bases com e-mails diferentes)
    if not func and nome:
        cur.execute("SELECT id FROM funcionarios WHERE nome = %s", (nome,))
        func = cur.fetchone()
        
    cur.close()
    conn.close()
    
    return True, (func["id"] if func else None), tipo


def _calcular_data_fim(valor: int, tipo: str) -> datetime:
    """Calcula data_estimativa_fim a partir do valor e tipo."""
    now = datetime.now()
    if tipo == "semanas":
        return now + timedelta(weeks=valor)
    elif tipo == "meses":
        return now + timedelta(days=valor * 30)
    elif tipo == "sessoes":
        # 1 sessão por semana como convenção
        return now + timedelta(weeks=valor)
    return now


# ─────────────────────────────────────────────
# PÁGINA PRINCIPAL
# ─────────────────────────────────────────────
@gestao_pacientes_bp.route("/")
def index():
    ok, _, _ = _require_medico()
    if not ok:
        return "Acesso restrito ao perfil clínico.", 403
    return render_template("gestao_pacientes.html")


# ─────────────────────────────────────────────
# API: LISTAR PACIENTES EM TRATAMENTO
# ─────────────────────────────────────────────
@gestao_pacientes_bp.route("/api/pacientes")
def api_listar_pacientes():
    ok, func_id, tipo = _require_medico()
    if not ok:
        return jsonify({"error": "Não autorizado"}), 403

    status_filtro = request.args.get("status", "EM_TRATAMENTO")

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        query = """
            SELECT
                pt.id                                           AS tratamento_id,
                pt.ciclo_id,
                pt.status,
                pt.estimativa_valor,
                pt.estimativa_tipo,
                TO_CHAR(pt.data_estimativa_inicio, 'DD/MM/YYYY') AS data_estimativa_inicio,
                TO_CHAR(pt.data_estimativa_fim,    'DD/MM/YYYY') AS data_estimativa_fim,
                TO_CHAR(pt.data_alta,              'DD/MM/YYYY') AS data_alta,
                pt.motivo_alta,
                pt.observacoes_alta,
                TO_CHAR(pt.criado_em,              'DD/MM/YYYY') AS data_inicio_tratamento,

                t.id          AS trabalhador_id,
                t.nome_completo AS paciente_nome,
                t.cpf         AS paciente_cpf,
                t.telefone    AS paciente_telefone,

                TO_CHAR(cc.data_inicio,            'DD/MM/YYYY') AS data_inicio_ciclo,
                TO_CHAR(cc.data_ultima_interacao,  'DD/MM/YYYY') AS ultima_interacao,
                cc.status     AS ciclo_status,

                f_med.nome    AS medico_nome,
                f_med.especialidade AS medico_especialidade,

                latest.especialidade_atual,
                latest.ultima_consulta

            FROM paciente_tratamento pt
            JOIN ciclo_cuidado cc        ON pt.ciclo_id       = cc.id
            JOIN trabalhadores t         ON pt.trabalhador_id = t.id
            LEFT JOIN funcionarios f_med ON pt.medico_id      = f_med.id

            LEFT JOIN LATERAL (
                SELECT
                    ae.especialidade AS especialidade_atual,
                    TO_CHAR(ae.data_consulta, 'DD/MM/YYYY') AS ultima_consulta
                FROM agendamento_exames ae
                WHERE ae.trabalhador_id = t.id
                ORDER BY ae.data_consulta DESC, ae.horario DESC
                LIMIT 1
            ) latest ON TRUE

            WHERE 1=1
        """
        params = []

        if status_filtro:
            query += " AND pt.status = %s"
            params.append(status_filtro)

        # Médico vê apenas os seus; Admin/Dev vê todos
        if tipo == "MEDICO":
            if func_id:
                query += " AND pt.medico_id = %s"
                params.append(func_id)
            else:
                # Se o perfil clínico não foi identificado, não mostra nenhum paciente (Segurança)
                query += " AND 1=0"

        query += " ORDER BY pt.criado_em DESC"

        cur.execute(query, params)
        rows = cur.fetchall()
        return jsonify(rows)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


# ─────────────────────────────────────────────
# API: DEFINIR / ATUALIZAR ESTIMATIVA
# ─────────────────────────────────────────────
@gestao_pacientes_bp.route("/api/estimativa/<int:tratamento_id>", methods=["POST"])
def api_definir_estimativa(tratamento_id):
    ok, func_id, tipo = _require_medico()
    if not ok:
        return jsonify({"error": "Não autorizado"}), 403

    data = request.get_json()
    valor = data.get("estimativa_valor")
    tipo_est = data.get("estimativa_tipo")

    if not valor or not tipo_est:
        return jsonify({"error": "Informe o valor e o tipo da estimativa."}), 400
    if tipo_est not in ("semanas", "meses", "sessoes"):
        return jsonify({"error": "Tipo inválido. Use: semanas, meses ou sessoes."}), 400

    data_fim = _calcular_data_fim(int(valor), tipo_est)

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Garante que só o médico responsável pode editar (ou admin/dev)
        # Se médico, pode editar se for o responsável OU se o paciente não tiver responsável ainda (assume o paciente)
        if tipo == "MEDICO" and func_id:
            cur.execute(
                "SELECT id FROM paciente_tratamento WHERE id = %s AND (medico_id = %s OR medico_id IS NULL) AND status = 'EM_TRATAMENTO'",
                (tratamento_id, func_id)
            )
            if not cur.fetchone():
                return jsonify({"error": "Permissão negada ou paciente já possui outro responsável."}), 403

        cur.execute("""
            UPDATE paciente_tratamento SET
                estimativa_valor        = %s,
                estimativa_tipo         = %s,
                data_estimativa_inicio  = NOW(),
                data_estimativa_fim     = %s,
                atualizado_em           = NOW(),
                atualizado_por          = %s,
                medico_id               = COALESCE(medico_id, %s)
            WHERE id = %s
        """, (valor, tipo_est, data_fim, session.get("email"), func_id, tratamento_id))

        conn.commit()
        return jsonify({"success": True, "data_estimativa_fim": data_fim.strftime("%d/%m/%Y")})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


# ─────────────────────────────────────────────
# API: DAR ALTA MÉDICA
# ─────────────────────────────────────────────
@gestao_pacientes_bp.route("/api/alta/<int:tratamento_id>", methods=["POST"])
def api_dar_alta(tratamento_id):
    ok, func_id, tipo = _require_medico()
    if not ok:
        return jsonify({"error": "Não autorizado"}), 403

    data = request.get_json()
    motivo    = data.get("motivo_alta", "Alta médica registrada pelo profissional.")
    observ    = data.get("observacoes_alta", "")

    if not motivo:
        return jsonify({"error": "O motivo da alta é obrigatório."}), 400

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Garante que apenas o médico responsável (ou admin/dev) dá alta
        # Se médico, pode dar alta se for o responsável OU se o paciente não tiver responsável ainda
        if tipo == "MEDICO" and func_id:
            cur.execute(
                "SELECT ciclo_id, trabalhador_id FROM paciente_tratamento WHERE id = %s AND (medico_id = %s OR medico_id IS NULL) AND status = 'EM_TRATAMENTO'",
                (tratamento_id, func_id)
            )
        else:
            cur.execute(
                "SELECT ciclo_id, trabalhador_id FROM paciente_tratamento WHERE id = %s AND status = 'EM_TRATAMENTO'",
                (tratamento_id,)
            )

        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Registro não encontrado ou você não tem permissão."}), 403

        ciclo_id       = row["ciclo_id"]
        trabalhador_id = row["trabalhador_id"]

        # 1. Atualiza paciente_tratamento
        cur.execute("""
            UPDATE paciente_tratamento SET
                status           = 'ALTA_MEDICA',
                data_alta        = NOW(),
                medico_alta_id   = %s,
                motivo_alta      = %s,
                observacoes_alta = %s,
                atualizado_em    = NOW(),
                atualizado_por   = %s
            WHERE id = %s
        """, (func_id, motivo, observ, session.get("email"), tratamento_id))

        # 2. Encerra ciclo_cuidado vinculado (sem deletar)
        cur.execute("""
            UPDATE ciclo_cuidado SET
                status              = 'ALTA',
                data_alta           = NOW(),
                medico_alta_id      = %s,
                observacao_alta     = %s,
                data_ultima_interacao = NOW()
            WHERE id = %s
        """, (func_id, observ, ciclo_id))

        # 3. Reseta flag de acolhimento do trabalhador (Exige novo acolhimento para futuro tratamento)
        cur.execute("""
            UPDATE trabalhadores SET
                acolhimento_realizado = FALSE
            WHERE id = %s
        """, (trabalhador_id,))

        conn.commit()
        return jsonify({"success": True})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


# ─────────────────────────────────────────────
# API: DETALHES DE UM PACIENTE
# ─────────────────────────────────────────────
@gestao_pacientes_bp.route("/api/paciente/<int:trabalhador_id>/historico")
def api_historico_paciente(trabalhador_id):
    ok, _, _ = _require_medico()
    if not ok:
        return jsonify({"error": "Não autorizado"}), 403

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # 1. Busca eventos de Agendamentos/Consultas
        cur.execute("""
            SELECT
                ae.id,
                'CONSULTA' AS tipo_evento,
                CAST(ae.data_consulta AS DATE) AS data_evento,
                TO_CHAR(ae.horario, 'HH24:MI') AS detalhe_horario,
                ae.especialidade,
                ae.status,
                ae.observacao,
                f.nome AS medico,
                ae.origem_agendamento
            FROM agendamento_exames ae
            JOIN funcionarios f ON ae.funcionario_id = f.id
            WHERE ae.trabalhador_id = %s
        """, (trabalhador_id,))
        consultas = cur.fetchall()

        # 2. Busca eventos de Início de Ciclo
        cur.execute("""
            SELECT
                'INICIO_CICLO' AS tipo_evento,
                CAST(data_inicio AS DATE) AS data_evento,
                NULL AS detalhe_horario,
                'Acolhimento QualiVida' AS especialidade,
                status,
                NULL AS observacao,
                NULL AS medico,
                NULL AS origem_agendamento
            FROM ciclo_cuidado
            WHERE trabalhador_id = %s
        """, (trabalhador_id,))
        ciclos = cur.fetchall()

        # 3. Busca eventos de Início de Tratamento Clínico
        cur.execute("""
            SELECT
                'INICIO_TRATAMENTO' AS tipo_evento,
                CAST(pt.criado_em AS DATE) AS data_evento,
                TO_CHAR(pt.criado_em, 'HH24:MI') AS detalhe_horario,
                f.especialidade,
                pt.status,
                NULL AS observacao,
                f.nome AS medico,
                NULL AS origem_agendamento
            FROM paciente_tratamento pt
            LEFT JOIN funcionarios f ON pt.medico_id = f.id
            WHERE pt.trabalhador_id = %s
        """, (trabalhador_id,))
        tratamentos = cur.fetchall()

        # Consolida e formata
        eventos = []
        
        # 4. Busca Desfechos Clínicos (Para enriquecer as consultas)
        cur.execute("""
            SELECT atendimento_id, tipo_desfecho, conduta, TO_CHAR(criado_em, 'DD/MM/YYYY HH24:MI') as data_reg
            FROM desfechos_clinicos
            WHERE paciente_id = %s
        """, (trabalhador_id,))
        desfechos = {d['atendimento_id']: d for d in cur.fetchall()}

        for c in consultas:
            # PULA agendamentos cancelados de regulação que não tiveram desfecho (Limpeza de ruído)
            if c['status'] == 'Cancelado' and c['origem_agendamento'] == 'REGULACAO' and not c['observacao']:
                continue
                
            desc = f"Consulta de {c['especialidade']}"
            icon = "calendar"
            color = "blue"
            
            if c['origem_agendamento'] == 'ENCAMINHAMENTO':
                desc = f"Encaminhamento para {c['especialidade']}"
                icon = "send"
                color = "indigo"
            elif c['especialidade'] == 'Acolhimento':
                desc = "Consulta de Acolhimento"
                icon = "heart-handshake"
                color = "emerald"
            
            # Enriquece com o desfecho se existir
            obs_timeline = c['observacao'] or ""
            df = desfechos.get(c['id'])
            if df:
                obs_timeline = f"<b>Conduta:</b> {df['conduta']}"
                if df['tipo_desfecho'] == 'encaminhar':
                    desc += " (C/ Encaminhamento)"
            
            h = c['detalhe_horario'] or "00:00"
            sort_dt = f"{c['data_evento']} {h}"
            
            eventos.append({
                "id": c['id'],
                "data": c['data_evento'].strftime("%d/%m/%Y"),
                "horario": c['detalhe_horario'],
                "titulo": desc,
                "profissional": c['medico'],
                "status": c['status'],
                "obs": obs_timeline,
                "tipo": "consulta",
                "icon": icon,
                "color": color,
                "raw_date": sort_dt
            })

        for cc in ciclos:
            eventos.append({
                "data": cc['data_evento'].strftime("%d/%m/%Y"),
                "horario": "--:--",
                "titulo": "Início do Ciclo de Cuidado",
                "profissional": "QualiVida",
                "status": cc['status'],
                "obs": "Paciente ingressou no fluxo de acolhimento.",
                "tipo": "sistema",
                "icon": "activity",
                "color": "sky",
                "raw_date": f"{cc['data_evento']} 00:00"
            })

        for pt in tratamentos:
            eventos.append({
                "data": pt['data_evento'].strftime("%d/%m/%Y"),
                "horario": pt['detalhe_horario'],
                "titulo": "Início de Tratamento Especializado",
                "profissional": pt['medico'],
                "status": pt['status'],
                "obs": "Paciente vinculado para acompanhamento clínico contínuo.",
                "tipo": "clinico",
                "icon": "heart-pulse",
                "color": "amber",
                "raw_date": f"{pt['data_evento']} {pt['detalhe_horario']}"
            })

        # Ordena por data e hora decrescente (mais recente primeiro)
        eventos.sort(key=lambda x: x['raw_date'], reverse=True)
        
        # Remove a chave raw_date antes de enviar
        for e in eventos:
            e.pop('raw_date')

        return jsonify(eventos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

