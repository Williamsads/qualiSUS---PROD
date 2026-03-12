import psycopg2

def migrate():
    conn = psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )
    cur = conn.cursor()
    
    try:
        print("Adicionando coluna atualizado_por em agendamento_exames...")
        cur.execute("ALTER TABLE agendamento_exames ADD COLUMN IF NOT EXISTS atualizado_por VARCHAR(255);")
        conn.commit()
        print("Sucesso!")
    except Exception as e:
        print(f"Erro: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate()
