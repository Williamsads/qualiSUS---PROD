import psycopg2
import sys

def promote_ana_fixed():
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cur = conn.cursor()
        
        email = "ana.souza.final@qualisus.com"
        
        print(f"Update: {email} -> tipo='medico'...")
        cur.execute("UPDATE usuarios SET tipo = 'medico', ativo = TRUE WHERE email = %s", (email,))
        conn.commit()
        
        cur.execute("SELECT tipo FROM usuarios WHERE email = %s", (email,))
        row = cur.fetchone()
        
        print("\nSUCESSO!")
        print(f"Email: {email}")
        print(f"Tipo atualizado: {row[0]}")
        print("Agora ela deve ver o botão de Atendimento!\n")
        
    except Exception as e:
        print(f"ERRO: {e}")
    finally:
        if 'conn' in locals(): conn.close()
        
if __name__ == "__main__":
    promote_ana_fixed()
