import psycopg2
from psycopg2.extras import RealDictCursor

def list_records_containing():
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        search_term = "1254845"
        
        print(f"--- Searching for '{search_term}' anywhere in workers or links ---")
        
        # Check numero_funcional with wildcard
        cur.execute("""
            SELECT t.nome_completo, vt.numero_funcional, t.cpf
            FROM vinculos_trabalhadores vt
            JOIN trabalhadores t ON vt.trabalhador_id = t.id
            WHERE vt.numero_funcional LIKE %s
        """, (f"%{search_term}%",))
        
        results_func = cur.fetchall()
        if results_func:
            print(f"\nFound in numero_funcional:")
            for r in results_func:
                print(f"  Nome: {r['nome_completo']} | Matrícula: {r['numero_funcional']} | CPF: {r['cpf']}")
        else:
            print("\nNot found in numero_funcional.")

        # Check CPF with wildcard
        cur.execute("""
            SELECT nome_completo, cpf
            FROM trabalhadores
            WHERE cpf LIKE %s
        """, (f"%{search_term}%",))
        
        results_cpf = cur.fetchall()
        if results_cpf:
            print(f"\nFound in CPF:")
            for r in results_cpf:
                print(f"  Nome: {r['nome_completo']} | CPF: {r['cpf']}")
        else:
            print("\nNot found in CPF.")
            
        # Inspect valid format of matriculas
        print("\n--- Sample Matriculas ---")
        cur.execute("SELECT numero_funcional FROM vinculos_trabalhadores WHERE numero_funcional IS NOT NULL LIMIT 5")
        for r in cur.fetchall():
            print(f"  '{r['numero_funcional']}'")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    list_records_containing()
