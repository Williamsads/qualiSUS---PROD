import psycopg2
import sys
import traceback

def create_user_try3():
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cur = conn.cursor()
        
        email = "ana.souza3@qualisus.com"
        senha = "123" 
        
        try:
            print("INSERT Usuario (Medico sem acento)...")
            cur.execute("""
                INSERT INTO usuarios (nome, email, senha, tipo, ativo) 
                VALUES ('Dra Ana 3', %s, %s, 'Medico', TRUE)
            """, (email, senha))
            
            print("INSERT Funcionario...")
            cur.execute("""
                INSERT INTO funcionarios 
                (nome, email, especialidade, unidade_atendimento, ativo, atendimento, situacao, cpf, telefone, data_nascimento, num_func_num_vinc)
                VALUES 
                ('Dra Ana 3', %s, 'Psicólogo', 'USF Centro', TRUE, TRUE, 'Ativo', '33333333333', '81333333333', '1985-05-15', 'FUNCANA3')
                RETURNING id
            """, (email,))
            func_id = cur.fetchone()[0]
            
            print("Vinculo Especialidade...")
            cur.execute("SELECT id FROM especialidades WHERE nome LIKE 'Psic%' LIMIT 1")
            esp = cur.fetchone()
            if esp:
                cur.execute("INSERT INTO funcionarios_especialidades (funcionario_id, especialidade_id) VALUES (%s, %s)", (func_id, esp[0]))
                
            conn.commit()
            print("\nSUCESSO: Usuario 'ana.souza3@qualisus.com' (senha '123') criado.\n")
            
        except Exception as e:
            conn.rollback()
            print(f"ERRO SQL: {e}")
            traceback.print_exc()
            
    except Exception as e:
        print(f"ERRO GERAL: {e}")
    finally:
        if 'conn' in locals(): conn.close()
        
if __name__ == "__main__":
    create_user_try3()
