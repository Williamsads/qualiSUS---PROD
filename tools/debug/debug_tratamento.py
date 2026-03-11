import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def check_treatment():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n--- PACIENTES EM TRATAMENTO ---")
    cur.execute("""
        SELECT pt.id, t.nome_completo, t.cpf, pt.status 
        FROM paciente_tratamento pt
        JOIN trabalhadores t ON pt.trabalhador_id = t.id
        WHERE pt.status = 'EM_TRATAMENTO'
    """)
    for row in cur.fetchall():
        print(row)
        
    print("\n--- AGENDAMENTOS ATIVOS (NÃO CANCELADOS) ---")
    cur.execute("""
        SELECT ae.id, t.nome_completo, ae.especialidade, ae.status 
        FROM agendamento_exames ae
        JOIN trabalhadores t ON ae.trabalhador_id = t.id
        WHERE ae.status != 'Cancelado'
    """)
    for row in cur.fetchall():
        print(row)
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_treatment()
