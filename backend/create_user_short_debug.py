import psycopg2
from werkzeug.security import generate_password_hash

def create_user_debug_short():
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cur = conn.cursor()
        
        email = "ana.souza@qualisus.com"
        senha = "123"
        senha_hash = generate_password_hash(senha) # Pode ser grande
        
        print(f"Tentando criar login: {email}")
        
        try:
            # Tenta Update 
            cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
            row = cur.fetchone()
            if row:
                print("Usuario existe. Atualizando...")
                cur.execute("UPDATE usuarios SET senha=%s WHERE id=%s", (senha_hash, row[0]))
            else:
                print("Criando usuario novo...")
                cur.execute("INSERT INTO usuarios (nome, email, senha, tipo, ativo) VALUES ('Dra. Ana Souza', %s, %s, 'Médico', TRUE)", (email, senha_hash))
            
            conn.commit()
            print("LOGIN OK")
            
        except Exception as e:
            print(f"ERRO SQL: {e}")
            conn.rollback()
        
    except Exception as e:
        print(f"ERRO CONEXAO: {e}")
    finally:
        if 'conn' in locals(): conn.close()
        
if __name__ == "__main__":
    create_user_debug_short()
