import os
import sys
import psycopg2
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
load_dotenv(os.path.join(os.path.dirname(__file__), '../backend/.env'))

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        database=os.getenv("DB_NAME", ""),
        user=os.getenv("DB_USER", ""),
        password=os.getenv("DB_PASSWORD", "")
    )

def main():
    print("Desfazendo a criação automática de especialidades e vínculos...")
    try:
        conn = get_connection()
        conn.autocommit = False
        cur = conn.cursor()
        
        # As especialidades criadas no script anterior ganharam IDs a partir do 40
        # O sistema tinha apenas 8 especialidades originais. Então qualquer ID >= 40 foi nossa injeção acidental.
        cur.execute("SELECT id FROM especialidades WHERE id >= 40")
        ids_to_remove = [r[0] for r in cur.fetchall()]
        
        if not ids_to_remove:
            print("Nenhuma especialidade recente (ID >= 40) encontrada para desfazer.")
            return
            
        print(f"IDs a serem revertidos e apagados: {ids_to_remove}")
        
        # 1. Resetar o campo na tabela Funcionarios de volta a nulo/vazio
        cur.execute("UPDATE funcionarios SET especialidade_id = NULL WHERE especialidade_id = ANY(%s)", (ids_to_remove,))
        
        # 2. Desfazer os vínculos na tabela intermediária N:N
        cur.execute("DELETE FROM funcionarios_especialidades WHERE especialidade_id = ANY(%s)", (ids_to_remove,))
        
        # 3. Remover a especialidade injetada
        cur.execute("DELETE FROM especialidades WHERE id = ANY(%s)", (ids_to_remove,))
        
        conn.commit()
        print("Rollback realizado com sucesso! O banco voltou exatamente ao estado anterior com os 16 funcionários em avulso.")
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"Erro ao desfazer: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    main()
