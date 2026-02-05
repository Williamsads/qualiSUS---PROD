import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def check_duplicates():
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        print("Checking for duplicates in 'funcionarios' table...")
        
        # Check by CPF
        cursor.execute("""
            SELECT cpf, COUNT(*) as count 
            FROM funcionarios 
            WHERE cpf IS NOT NULL AND cpf != ''
            GROUP BY cpf 
            HAVING COUNT(*) > 1
        """)
        dup_cpf = cursor.fetchall()
        
        # Check by Matrícula
        cursor.execute("""
            SELECT num_func_num_vinc, COUNT(*) as count 
            FROM funcionarios 
            WHERE num_func_num_vinc IS NOT NULL AND num_func_num_vinc != ''
            GROUP BY num_func_num_vinc 
            HAVING COUNT(*) > 1
        """)
        dup_mat = cursor.fetchall()
        
        # Check by Name
        cursor.execute("""
            SELECT nome, COUNT(*) as count 
            FROM funcionarios 
            GROUP BY nome 
            HAVING COUNT(*) > 1
        """)
        dup_nome = cursor.fetchall()

        if not dup_cpf and not dup_mat and not dup_nome:
            print("No duplicates found by CPF, Matrícula, or Name.")
        else:
            if dup_cpf:
                print(f"\nDuplicates by CPF:\n{dup_cpf}")
            if dup_mat:
                print(f"\nDuplicates by Matrícula:\n{dup_mat}")
            if dup_nome:
                print(f"\nDuplicates by Name:\n{dup_nome}")

            # detailed info for some duplicates
            if dup_nome:
                print("\nDetailed duplicate info (example by name):")
                for d in dup_nome[:3]:
                    cursor.execute("SELECT id, nome, cpf, num_func_num_vinc, especialidade FROM funcionarios WHERE nome = %s", (d['nome'],))
                    rows = cursor.fetchall()
                    print(f"Name: {d['nome']}")
                    for r in rows:
                        print(f"  - ID: {r['id']}, CPF: {r['cpf']}, Mat: {r['num_func_num_vinc']}, Esp: {r['especialidade']}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_duplicates()
