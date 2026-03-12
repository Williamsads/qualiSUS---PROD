import psycopg2
from psycopg2.extras import RealDictCursor

def check_funcionarios_and_tables():
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = [row['table_name'] for row in cur.fetchall()]
        print(f"Tables: {tables}")
        
        # Check funcionarios table for the number
        print("\n--- Checking 'funcionarios' table ---")
        search_term = "1254845"
        
        # We don't know the columns yet, let's look at schema of funcionarios
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'funcionarios'
        """)
        cols = [row['column_name'] for row in cur.fetchall()]
        print(f"Columns in funcionarios: {cols}")
        
        # Search in likely columns
        term_wild = f"%{search_term}%"
        query = f"""
            SELECT * FROM funcionarios 
            WHERE 
                (nome::text LIKE '{term_wild}') OR
                (cpf::text LIKE '{term_wild}') OR
                (num_func_num_vinc::text LIKE '{term_wild}')
        """
        cur.execute(query)
        results = cur.fetchall()
        
        if results:
            print(f"\nFound in 'funcionarios':")
            for r in results:
                print(f"  Nome: {r.get('nome')} | CPF: {r.get('cpf')} | Matr: {r.get('num_func_num_vinc')}")
        else:
            print("\nNot found in 'funcionarios'.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    check_funcionarios_and_tables()
