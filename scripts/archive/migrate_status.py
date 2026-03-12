
import psycopg2
from psycopg2 import sql

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
            WHERE table_name='vinculos_trabalhadores' AND column_name='situacao';
        """)
        
        if not cur.fetchone():
            print("Adicionando coluna 'situacao' na tabela vinculos_trabalhadores...")
            cur.execute("""
                ALTER TABLE vinculos_trabalhadores
                ADD COLUMN situacao VARCHAR(50) DEFAULT 'Ativo';
            """)
            conn.commit()
            print("Coluna adicionada com sucesso!")
        else:
            print("Coluna 'situacao' já existe.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro na migração: {e}")

if __name__ == "__main__":
    migrate()
