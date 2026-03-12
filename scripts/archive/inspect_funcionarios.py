import psycopg2

def inspect_db():
    conn = psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )
    cur = conn.cursor()
    
    # Listar colunas da tabela funcionarios
    cur.execute("""
        SELECT column_name, is_nullable, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'funcionarios';
    """)
    for row in cur.fetchall():
        print(row)
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    inspect_db()
