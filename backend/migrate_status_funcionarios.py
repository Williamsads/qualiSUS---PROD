
import psycopg2

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def migrate():
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Check if column exists
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='funcionarios' AND column_name='situacao';
        """)
        
        if not cur.fetchone():
            print("Adicionando coluna 'situacao' na tabela funcionarios...")
            cur.execute("""
                ALTER TABLE funcionarios
                ADD COLUMN situacao VARCHAR(50) DEFAULT 'Ativo';
            """)
            conn.commit()
            print("Coluna adicionada com sucesso!")
        else:
            print("Coluna 'situacao' já existe na tabela funcionarios.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro na migração: {e}")

if __name__ == "__main__":
    migrate()
