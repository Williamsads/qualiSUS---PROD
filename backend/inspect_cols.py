import psycopg2
import json

def inspect_db():
    try:
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
        
        rows = cur.fetchall()
        
        with open("funcionarios_cols.txt", "w", encoding="utf-8") as f:
            for row in rows:
                f.write(f"{row}\n")
            
        cur.close()
        conn.close()
        print("Arquivo funcionarios_cols.txt salvo.")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    inspect_db()
