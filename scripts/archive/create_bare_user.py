import psycopg2
import sys

def create_bare_user():
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cur = conn.cursor()
        
        email = "psi.teste@qualisus.com"
        senha = "123" # Apenas teste de insert
        
        sql = "INSERT INTO usuarios (nome, email, senha, tipo, ativo) VALUES ('Psico Teste', %s, %s, 'Médico', TRUE)"
        
        try:
            cur.execute(sql, (email, senha))
            conn.commit()
            print("USUARIO CRIADO COM SUCESSO (Senha plain: 123)")
        except Exception as e:
            conn.rollback()
            sys.stderr.write(f"ERRO SQL: {e}\n")
            
    except Exception as e:
        sys.stderr.write(f"ERRO GERAL: {e}\n")
    finally:
        f 'conn' in locals(): conn.close()
        
if __name__ == "__main__":
    create_bare_user()
