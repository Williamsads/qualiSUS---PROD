
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
        
        # Check if columns exist
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='funcionarios' AND column_name IN ('situacao_data_inicio', 'situacao_data_fim');
        """)
        
        existing_columns = [row[0] for row in cur.fetchall()]
        
        if 'situacao_data_inicio' not in existing_columns:
            print("Adicionando coluna 'situacao_data_inicio' na tabela funcionarios...")
            cur.execute("""
                ALTER TABLE funcionarios
                ADD COLUMN situacao_data_inicio DATE;
            """)
            print("Coluna 'situacao_data_inicio' adicionada!")
        else:
            print("Coluna 'situacao_data_inicio' já existe.")
            
        if 'situacao_data_fim' not in existing_columns:
            print("Adicionando coluna 'situacao_data_fim' na tabela funcionarios...")
            cur.execute("""
                ALTER TABLE funcionarios
                ADD COLUMN situacao_data_fim DATE;
            """)
            print("Coluna 'situacao_data_fim' adicionada!")
        else:
            print("Coluna 'situacao_data_fim' já existe.")
        
        conn.commit()
        cur.close()
        conn.close()
        print("Migração concluída com sucesso!")
    except Exception as e:
        print(f"Erro na migração: {e}")

if __name__ == "__main__":
    migrate()
