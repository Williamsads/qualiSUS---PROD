import psycopg2

def list_types():
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cur = conn.cursor()
        
        print("Tipos existentes na tabela usuarios:")
        cur.execute("SELECT DISTINCT tipo FROM usuarios")
        rows = cur.fetchall()
        for row in rows:
            print(f"- {row[0]}")
            
    except Exception as e:
        print(f"ERRO: {e}")
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    list_types()
