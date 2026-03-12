import psycopg2
from werkzeug.security import generate_password_hash
import traceback

def create_user_debug():
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
        senha_hash = generate_password_hash(senha)
        
        print(f"Tentando criar login: {email}")
        
        # Tenta inserir
        cur.execute("""
            INSERT INTO usuarios (nome, email, senha, tipo, ativo) 
            VALUES ('Dra. Ana Souza', %s, %s, 'Médico', TRUE)
        """, (email, senha_hash))
        
        conn.commit()
        print("LOGIN CRIADO COM SUCESSO!")
        
    except Exception:
        with open("error_login.txt", "w") as f:
            traceback.print_exc(file=f)
        print("Erro gravado em error_login.txt")
    finally:
        if 'conn' in locals(): conn.close()
        
if __name__ == "__main__":
    create_user_debug()
