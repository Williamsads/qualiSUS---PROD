import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def check_links():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Check specialty ID for 'Terapeuta Ocupacional'
    cur.execute("SELECT id FROM especialidades WHERE nome ILIKE '%Terapeuta Ocupacional%'")
    spec = cur.fetchone()
    if not spec:
        print("Specialty not found")
        return
    
    spec_id = spec['id']
    print(f"Specialty ID: {spec_id}")
    
    # Check if linked to any unit
    cur.execute("SELECT u.nome FROM unidades_saude u JOIN unidades_especialidades ue ON ue.unidade_id = u.id WHERE ue.especialidade_id = %s", (spec_id,))
    units = cur.fetchall()
    print(f"Linked units: {[u['nome'] for u in units]}")
    
    # Check if any professional has this specialty
    cur.execute("SELECT f.nome FROM funcionarios f JOIN funcionarios_especialidades fe ON fe.funcionario_id = f.id WHERE fe.especialidade_id = %s", (spec_id,))
    profs = cur.fetchall()
    print(f"Professionals with this specialty: {[p['nome'] for p in profs]}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_links()
