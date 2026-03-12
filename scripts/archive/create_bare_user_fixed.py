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
        
        try:
            print("INSERT Usuario...")
            cur.execute("""
                INSERT INTO usuarios (nome, email, senha, tipo, ativo) 
                VALUES ('Psico Teste', %s, %s, 'Médico', TRUE)
            """, (email, senha))
            
            print("INSERT Funcionario...")
            cur.execute("""
                INSERT INTO funcionarios 
                (nome, email, especialidade, unidade_atendimento, ativo, atendimento, situacao, cpf, telefone, data_nascimento, num_func_num_vinc)
                VALUES 
                ('Psico Teste', %s, 'Psicólogo', 'USF Centro', TRUE, TRUE, 'Ativo', '99999999999', '99999999999', '1990-01-01', 'FUNCTESTE')
                RETURNING id
            """, (email,))
            func_id = cur.fetchone()[0]
            
            print("Vinculo Especialidade...")
            cur.execute("SELECT id FROM especialidades WHERE nome = 'Psicólogo'")
            esp = cur.fetchone()
            if esp:
                cur.execute("INSERT INTO funcionarios_especialidades (funcionario_id, especialidade_id) VALUES (%s, %s)", (func_id, esp[0]))
                
            conn.commit()
            print("\nSUCESSO: Usuario 'psi.teste@qualisus.com' senha '123' criado e vinculado.\n")
            
        except Exception as e:
            conn.rollback()
            print(f"ERRO SQL: {e}", file=sys.stderr)
            
    except Exception as e:
        print(f"ERRO GERAL: {e}", file=sys.stderr)
    finally:
        if 'conn' in locals(): conn.close()
        
if __name__ == "__main__":
    create_bare_user()
