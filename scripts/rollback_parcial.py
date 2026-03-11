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
    print("Iniciando Restauração Parcial (Apenas Cadastros)...")
    try:
        conn = get_connection()
        conn.autocommit = False
        cur = conn.cursor()
        
        # Inserir de volta os trabalhadores (pacientes base)
        cur.execute("INSERT INTO trabalhadores SELECT * FROM backup_20260309_trabalhadores;")
        
        # Inserir de volta os vínculos (já que a busca pode depender deles)
        cur.execute("INSERT INTO vinculos_trabalhadores SELECT * FROM backup_20260309_vinculos_trabalhadores;")
        
        conn.commit()
        print("Trabalhadores e Vínculos restaurados com sucesso!")
        
        cur.execute("SELECT COUNT(*) FROM trabalhadores;")
        t_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM vinculos_trabalhadores;")
        v_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM agendamento_exames;")
        a_count = cur.fetchone()[0]
        
        print(f"Total de Trabalhadores agora: {t_count}")
        print(f"Total de Vínculos agora: {v_count}")
        print(f"Total de Agendamentos (continua limpo): {a_count}")
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"Erro: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    main()
