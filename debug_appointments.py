import psycopg2
from psycopg2.extras import RealDictCursor

def list_appointments():
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check agendamentos
        cur.execute("""
            SELECT 
                a.id, 
                a.paciente_id, 
                t.nome_completo, 
                t.cpf, 
                vt.numero_funcional
            FROM agendamentos a
            LEFT JOIN trabalhadores t ON a.paciente_id = t.id
            LEFT JOIN vinculos_trabalhadores vt ON vt.trabalhador_id = t.id
            LIMIT 5
        """)
        
        print("\n--- Agendamentos Existentes ---")
        for r in cur.fetchall():
            print(f"Agendam ID: {r['id']}")
            print(f"  Paciente: {r['nome_completo']}")
            print(f"  CPF: {r['cpf']}")
            print(f"  Matricula: {r['numero_funcional']}")
            print("-" * 20)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    list_appointments()
