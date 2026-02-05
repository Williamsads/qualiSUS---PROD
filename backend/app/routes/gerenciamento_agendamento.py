from flask import Blueprint, render_template, request, jsonify, session
import psycopg2
from psycopg2.extras import RealDictCursor

gerenciamento_bp = Blueprint('gerenciamento', __name__)

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

@gerenciamento_bp.route("/gerenciamento/agendamento")
def index():
    if "user_id" not in session:
        return jsonify({"error": "Não autorizado"}), 401
    return render_template("gerenciamento_agendamento.html")

# --- FILTRO CRUZADO ---
@gerenciamento_bp.route("/api/gerenciamento/especialidades-por-unidade", methods=["GET"])
def list_especialidades_por_unidade():
    unidade = request.args.get('unidade')
    if not unidade:
        return jsonify([])
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT DISTINCT e.nome 
            FROM funcionarios f 
            JOIN especialidades e ON f.especialidade_id = e.id 
            WHERE f.unidade_atendimento = %s AND f.ativo = true
            ORDER BY e.nome
        """, (unidade,))
        rows = cur.fetchall()
        # Retorna uma lista simples de nomes: ["Cardiologia", "Pediatria", ...]
        return jsonify(rows) 
    except Exception as e:
        print(f"Error fetching specialties for unit: {e}")
        return jsonify([])
    finally:
        cur.close()
        conn.close()

# --- UNIDADES ---
@gerenciamento_bp.route("/api/gerenciamento/unidades", methods=["GET"])
def list_unidades():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, nome, endereco FROM unidades_saude ORDER BY nome")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)

@gerenciamento_bp.route("/api/gerenciamento/unidades", methods=["POST"])
def add_unidade():
    data = request.json
    nome = data.get("nome")
    endereco = data.get("endereco")
    
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO unidades_saude (nome, endereco) VALUES (%s, %s)", (nome, endereco))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@gerenciamento_bp.route("/api/gerenciamento/unidades/<int:id>", methods=["PUT"])
def update_unidade(id):
    data = request.json
    nome = data.get("nome")
    endereco = data.get("endereco")
    
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE unidades_saude SET nome = %s, endereco = %s WHERE id = %s", (nome, endereco, id))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@gerenciamento_bp.route("/api/gerenciamento/unidades/<int:id>", methods=["DELETE"])
def delete_unidade(id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM unidades_saude WHERE id = %s", (id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


# --- ESPECIALIDADES ---
@gerenciamento_bp.route("/api/gerenciamento/especialidades", methods=["GET"])
def list_especialidades():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM especialidades ORDER BY nome")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)

@gerenciamento_bp.route("/api/gerenciamento/especialidades", methods=["POST"])
def add_especialidade():
    data = request.json
    nome = data.get("nome")
    icone = data.get("icone", "stethoscope")
    vincular_todas = data.get("vincular_todas", False)
    
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO especialidades (nome, icone) VALUES (%s, %s) RETURNING id", (nome, icone))
        new_id = cur.fetchone()[0]
        
        if vincular_todas:
            # Vincula a todas as unidades existentes
            cur.execute("INSERT INTO unidades_especialidades (unidade_id, especialidade_id) SELECT id, %s FROM unidades_saude", (new_id,))
            
        conn.commit()
        return jsonify({"success": True, "id": new_id})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@gerenciamento_bp.route("/api/gerenciamento/especialidades/<int:id>", methods=["PUT"])
def update_especialidade(id):
    data = request.json
    nome = data.get("nome")
    icone = data.get("icone")
    
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE especialidades SET nome = %s, icone = %s WHERE id = %s", (nome, icone, id))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@gerenciamento_bp.route("/api/gerenciamento/especialidades/<int:id>", methods=["DELETE"])
def delete_especialidade(id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # First unlink professionals from this specialty to avoid FK violation
        cur.execute("UPDATE funcionarios SET especialidade_id = NULL WHERE especialidade_id = %s", (id,))
        
        # Then delete the specialty
        cur.execute("DELETE FROM especialidades WHERE id = %s", (id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

# --- UNIT-SPECIALTY LINKING ---
@gerenciamento_bp.route("/api/gerenciamento/unidades/<int:id>/especialidades", methods=["GET"])
def get_unit_specialties(id):
    conn = get_connection()
    cur = conn.cursor() # Returns tuples
    cur.execute("SELECT especialidade_id FROM unidades_especialidades WHERE unidade_id = %s", (id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    # Return list of IDs: [1, 5, 10]
    return jsonify([row[0] for row in rows])

@gerenciamento_bp.route("/api/gerenciamento/unidades/<int:id>/especialidades", methods=["POST"])
def set_unit_specialties(id):
    data = request.json
    specialty_ids = data.get("especialidade_ids", [])
    
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Transaction: Clear existing -> Insert new
        cur.execute("DELETE FROM unidades_especialidades WHERE unidade_id = %s", (id,))
        
        if specialty_ids:
            # Efficient batch insert
            args = [(id, esp_id) for esp_id in specialty_ids]
            # Manual mogrify to support older psycopg2 or ensure compatibility
            args_str = ','.join(cur.mogrify("(%s,%s)", x).decode('utf-8') for x in args)
            cur.execute("INSERT INTO unidades_especialidades (unidade_id, especialidade_id) VALUES " + args_str)
            
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

# --- PROFISSIONAIS (FUNCIONARIOS) ---
@gerenciamento_bp.route("/api/gerenciamento/profissionais", methods=["GET"])
@gerenciamento_bp.route("/api/gerenciamento/profissionais", methods=["GET"])
def list_profissionais():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    # Get professionals with their specialties as a JSON array (PostgreSQL specific aggregation)
    cur.execute("""
        SELECT f.*, 
               COALESCE(
                   (SELECT json_agg(json_build_object('id', e.id, 'nome', e.nome))
                    FROM funcionarios_especialidades fe
                    JOIN especialidades e ON fe.especialidade_id = e.id
                    WHERE fe.funcionario_id = f.id),
                   '[]'::json
               ) as especialidades
        FROM funcionarios f 
        ORDER BY f.nome
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)

@gerenciamento_bp.route("/api/gerenciamento/profissionais", methods=["POST"])
def add_profissional():
    data = request.json
    nome = data.get("nome")
    especialidade_ids = data.get("especialidade_ids", [])
    if not especialidade_ids and data.get("especialidade_id"):
        especialidade_ids = [data.get("especialidade_id")]

    unidade = data.get("unidade_atendimento")
    ativo = data.get("ativo", True)
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Keep single columns updated with the first one for compatibility
        first_id = especialidade_ids[0] if especialidade_ids else None
        cur.execute("SELECT nome FROM especialidades WHERE id = %s", (first_id,))
        esp_row = cur.fetchone()
        especialidade_nome = esp_row['nome'] if esp_row else 'Clínico Geral'

        cur.execute("""
            INSERT INTO funcionarios (
                nome, especialidade_id, especialidade, unidade_atendimento, ativo,
                cpf, num_func_num_vinc, data_nascimento, email, telefone, atendimento
            ) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            nome, first_id, especialidade_nome, unidade, ativo,
            '00000000000', '00000', '1980-01-01', 'medico@qualivida.com', '81999999999', True
        ))
        new_id = cur.fetchone()['id']

        # Add all specialties to bridge table
        for e_id in especialidade_ids:
            cur.execute("INSERT INTO funcionarios_especialidades (funcionario_id, especialidade_id) VALUES (%s, %s)", (new_id, e_id))

        conn.commit()
        return jsonify({"success": True, "id": new_id})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@gerenciamento_bp.route("/api/gerenciamento/profissionais/<int:id>", methods=["PUT"])
def update_profissional(id):
    data = request.json
    nome = data.get("nome")
    especialidade_ids = data.get("especialidade_ids", [])
    if not especialidade_ids and data.get("especialidade_id"):
        especialidade_ids = [data.get("especialidade_id")]

    unidade = data.get("unidade_atendimento")
    ativo = data.get("ativo")
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Keep single columns updated for compatibility
        first_id = especialidade_ids[0] if especialidade_ids else None
        cur.execute("SELECT nome FROM especialidades WHERE id = %s", (first_id,))
        esp_row = cur.fetchone()
        especialidade_nome = esp_row['nome'] if esp_row else 'Clínico Geral'

        cur.execute("""
            UPDATE funcionarios 
            SET nome = %s, especialidade_id = %s, especialidade = %s, unidade_atendimento = %s, ativo = %s 
            WHERE id = %s
        """, (nome, first_id, especialidade_nome, unidade, ativo, id))

        # Update bridge table
        cur.execute("DELETE FROM funcionarios_especialidades WHERE funcionario_id = %s", (id,))
        for e_id in especialidade_ids:
            cur.execute("INSERT INTO funcionarios_especialidades (funcionario_id, especialidade_id) VALUES (%s, %s)", (id, e_id))

        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@gerenciamento_bp.route("/api/gerenciamento/profissionais/<int:id>", methods=["DELETE"])
def delete_profissional(id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM funcionarios WHERE id = %s", (id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

# --- HORÁRIOS DOS PROFISSIONAIS ---
@gerenciamento_bp.route("/api/gerenciamento/horarios/<int:prof_id>", methods=["GET"])
def list_horarios(prof_id):
    dia = request.args.get('dia') # Opcional: filtro para a tela de reserva
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    if dia:
        cur.execute("""
            SELECT id, TO_CHAR(horario, 'HH24:MI') as horario, dia_semana 
            FROM horarios_funcionarios 
            WHERE funcionario_id = %s AND dia_semana = %s
            ORDER BY horario
        """, (prof_id, dia))
    else:
        cur.execute("""
            SELECT id, TO_CHAR(horario, 'HH24:MI') as horario, dia_semana 
            FROM horarios_funcionarios 
            WHERE funcionario_id = %s 
            ORDER BY dia_semana, horario
        """, (prof_id,))
        
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)

@gerenciamento_bp.route("/api/gerenciamento/horarios", methods=["POST"])
def add_horario():
    data = request.json
    prof_id = data.get("funcionario_id")
    horario = data.get("horario")
    dia_semana = data.get("dia_semana")
    
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO horarios_funcionarios (funcionario_id, horario, dia_semana) VALUES (%s, %s, %s)", (prof_id, horario, dia_semana))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@gerenciamento_bp.route("/api/gerenciamento/horarios/<int:id>", methods=["DELETE"])
def delete_horario(id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM horarios_funcionarios WHERE id = %s", (id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

