from flask import Blueprint, request, jsonify, render_template, session, redirect
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

painel_bp = Blueprint("painel_bp", __name__, template_folder="templates")

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

@painel_bp.route("/painel_profissional")
def pagina_painel():
    if not session.get("user_id"):
        return redirect("/index")
    # Aqui poderia ter verificação de tipo de profissional
    return render_template("painel_profissional.html")

@painel_bp.route("/api/painel/pacientes")
def listar_pacientes():
    if not session.get("user_id"):
        return jsonify({"error": "Sessão expirada"}), 401
    
    # Busca o ID do profissional logado
    user_email = session.get("email")
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("SELECT id, especialidade FROM funcionarios WHERE email = %s", (user_email,))
        profissional = cur.fetchone()
        
        if not profissional:
            return jsonify({"error": "Profissional não encontrado"}), 403
            
        profissional_id = profissional['id']
        
        # Buscar pacientes em tratamento e não 'Em tratamento'
        # Regra do cliente: "listar todos os pacientes em acompanhamento"
        # Vou assumir ativos e históricos
        
        # Busca pacientes que têm agendamento COM ESTE profissional
        # Faz LEFT JOIN com tratamentos para saber se já tem plano
        cur.execute("""
            SELECT 
                t.id as tratamento_id,
                tr.id as trabalhador_id,
                tr.nome_completo as nome_paciente,
                TO_CHAR(t.data_inicio, 'DD/MM/YYYY') as data_inicio,
                t.frequencia,
                TO_CHAR(MAX(ae.data_consulta), 'DD/MM/YYYY') as data_ultima_consulta,
                COALESCE(t.status, 'Aguardando Início') as status
            FROM agendamento_exames ae
            JOIN trabalhadores tr ON ae.trabalhador_id = tr.id
            LEFT JOIN tratamentos t ON t.trabalhador_id = ae.trabalhador_id AND t.funcionario_id = ae.funcionario_id
            WHERE ae.funcionario_id = %s
              AND ae.status != 'Cancelado'
            GROUP BY t.id, tr.id, tr.nome_completo, t.data_inicio, t.frequencia, t.status
            ORDER BY 
                CASE WHEN t.status = 'Em tratamento' THEN 1 
                     WHEN t.status IS NULL THEN 2 
                     ELSE 3 END,
                MAX(ae.data_consulta) DESC
        """, (profissional_id,))
        
        pacientes = cur.fetchall()
        
        return jsonify({
            "pacientes": pacientes,
            "especialidade": profissional["especialidade"]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@painel_bp.route("/api/painel/iniciar_tratamento", methods=["POST"])
def iniciar_tratamento():
    if not session.get("user_id"):
        return jsonify({"error": "Sessão expirada"}), 401
    
    data = request.json
    trabalhador_id = data.get("trabalhador_id")
    frequencia = data.get("frequencia")
    data_inicio = data.get("data_inicio")
    
    user_email = session.get("email")
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("SELECT id FROM funcionarios WHERE email = %s", (user_email,))
        profissional = cur.fetchone()
        
        if not profissional:
            return jsonify({"error": "Profissional não encontrado"}), 403
            
        # Verifica se já existe tratamento ativo
        cur.execute("""
            SELECT id FROM tratamentos 
            WHERE trabalhador_id = %s AND funcionario_id = %s AND status = 'Em tratamento'
        """, (trabalhador_id, profissional['id']))
        existe = cur.fetchone()
        if existe:
            # Apenas atualiza
            cur.execute("""
                UPDATE tratamentos SET frequencia = %s, data_inicio = %s
                WHERE id = %s
            """, (frequencia, data_inicio, existe['id']))
        else:
            # Cria novo
            cur.execute("""
                INSERT INTO tratamentos (trabalhador_id, funcionario_id, data_inicio, frequencia, status)
                VALUES (%s, %s, %s, %s, 'Em tratamento')
            """, (trabalhador_id, profissional['id'], data_inicio, frequencia))
        
        conn.commit()
        return jsonify({"success": True})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@painel_bp.route("/api/painel/alta", methods=["POST"])
def dar_alta():
    if not session.get("user_id"):
        return jsonify({"error": "Sessão expirada"}), 401
    
    data = request.json
    tratamento_id = data.get("tratamento_id")
    data_alta = data.get("data_alta")
    observacao = data.get("observacao")
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Atualiza tratamento
        cur.execute("""
            UPDATE tratamentos 
            SET status = 'Alta', data_alta = %s, observacao_alta = %s
            WHERE id = %s
        """, (data_alta, observacao, tratamento_id))
        
        # Bloqueio: Deve registrar que o paciente não pode agendar sem novo acolhimento
        # O sistema de agendamento já deve verificar se o 'ciclo_cuidado' ou 'validado_para_psico' está ativo.
        # Aqui vamos desabilitar a aptidão
        
        # Busca trabalhador_id do tratamento
        cur.execute("SELECT trabalhador_id FROM tratamentos WHERE id = %s", (tratamento_id,))
        row = cur.fetchone()
        if row:
            trabalhador_id = row[0]
            # Desabilita TODOS os acolhimentos anteriores para forçar novo acolhimento
            cur.execute("""
                UPDATE agendamento_exames 
                SET validado_para_psico = FALSE 
                WHERE trabalhador_id = %s AND especialidade = 'Acolhimento'
            """, (trabalhador_id,))
            
        conn.commit()
        return jsonify({"success": True})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

# Rota auxiliar para preencher modal de Iniciar Tratamento com pacientes que agendaram e não têm tratamento
@painel_bp.route("/api/painel/pacientes_sem_tratamento")
def pacientes_sem_tratamento():
    if not session.get("user_id"):
        return jsonify({"error": "Sessão expirada"}), 401
    
    user_email = session.get("email")
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("SELECT id FROM funcionarios WHERE email = %s", (user_email,))
        profissional = cur.fetchone()
        
        if not profissional:
            return jsonify({"error": "Profissional não encontrado"}), 403
            
        # Busca pacientes que têm agendamento com este profissional MAS não têm tratamento ativo
        cur.execute("""
            SELECT DISTINCT 
                t.id as trabalhador_id, 
                t.nome_completo,
                MAX(ae.data_consulta) as ultima_consulta
            FROM agendamento_exames ae
            JOIN trabalhadores t ON ae.trabalhador_id = t.id
            WHERE ae.funcionario_id = %s 
              AND ae.status != 'Cancelado'
              AND NOT EXISTS (
                  SELECT 1 FROM tratamentos tr 
                  WHERE tr.trabalhador_id = t.id 
                    AND tr.funcionario_id = %s 
                    AND tr.status = 'Em tratamento'
              )
            GROUP BY t.id, t.nome_completo
            ORDER BY ultima_consulta DESC
        """, (profissional['id'], profissional['id']))
        
        pacientes = cur.fetchall()
        return jsonify({"pacientes": pacientes})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()
