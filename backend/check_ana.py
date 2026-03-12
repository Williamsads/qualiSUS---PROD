import psycopg2

def check_ana():
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cur = conn.cursor()
        
        email = "ana.souza.final@qualisus.com"
        
        cur.execute("SELECT nome, email, tipo, ativo FROM usuarios WHERE email = %s", (email,))
        row = cur.fetchone()
        
        if row:
            print("=== USUARIO ENCONTRADO ===")
            print(f"Nome: {row[0]}")
            print(f"Email: {row[1]}")
            print(f"Tipo: {row[2]}")
            print(f"Ativo: {row[3]}")
            print("==========================")
        else:
            print("Usuario nao encontrado")
        
    except Exception as e:
        print(f"ERRO: {e}")
    finally:
        if 'conn' in locals(): 
            conn.close()
        
if __name__ == "__main__":
    check_ana()
