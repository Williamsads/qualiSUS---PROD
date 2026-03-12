import psycopg2

def promote_ana():
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cur = conn.cursor()
        
        email = "ana.souza.final@qualisus.com"
        
        print(f"Buscando tipo atual de {email}...")
        cur.execute("SELECT tipo FROM usuarios WHERE email = %s", (email,))
        row = cur.fetchone()
        print(f"Tipo atual: {row[0] if row else 'Nao encontrado'}")
        
        print("Promovendo Dra Ana para 'medico'...")
        cur.execute("UPDATE usuarios SET tipo = 'medico' WHERE email = %s", (email,))
        conn.commit()
        
        cur.execute("SELECT tipo FROM usuarios WHERE email = %s", (email,))
        new_row = cur.fetchone()
        print(f"Novo Tipo: {new_row[0]}")
        
    except Exception as e:
        print(f"ERRO: {e}")
    finally:
        f 'conn' in locals(): conn.close()

if __name__ == "__main__":
    promote_ana()
