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
    print("Iniciando Limpeza de Dados de Pacientes...")
    print("Conectando ao banco de dados...")
    
    try:
        conn = get_connection()
        conn.autocommit = False
        cur = conn.cursor()
        
        # Lê o script SQL criado anteriormente
        sql_path = os.path.join(os.path.dirname(__file__), 'limpeza_pacientes.sql')
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # Executa a limpeza e os backups
        print("Criando backup e limpando (TRUNCATE CASCADE)...")
        # Divide as queries e roda a validação no final separadamente para imprimir o resultado
        queries = sql_script.split(';')
        
        for q in queries[:-2]: # pula os dois ultimos splits vazios/SELECTs
            q = q.strip()
            if q:
                if q.upper().startswith("SELECT"):
                    break # para na query de relatório
                print(f"Executando parte do script...")
                cur.execute(q)
                
        # Commit para salvar os deletes
        conn.commit()
        print("\nLimpeza concluída com sucesso! Resultados pós-limpeza:")
        
        # Executar a query de relatório
        relatorio_query = [q for q in queries if "SELECT" in q and "Trabalhadores" in q][0]
        cur.execute(relatorio_query)
        rows = cur.fetchall()
        print("-" * 60)
        print(f"{'Tabela':<30} | {'Restantes':<10} | {'Esperado'}")
        print("-" * 60)
        for row in rows:
            print(f"{row[0]:<30} | {row[1]:<10} | {row[2]}")
        print("-" * 60)
            
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"ERRO CRÍTICO NA LIMPEZA: {e}")
        print("=> Rollback realizado. Nada foi alterado.")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
