import psycopg2
import traceback

def debug_insert():
    try:
        conn = psycopg2.connect(
             host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cur = conn.cursor()
        
        print("Tentando INSERT simples...")
        
        sql = """
            INSERT INTO funcionarios 
            (nome, email, especialidade, unidade_atendimento, ativo, atendimento, situacao, cpf, telefone, data_nascimento, num_func_num_vinc)
            VALUES 
            ('Teste Debug', 'teste@debug.com', 'Psicólogo', 'USF Centro', TRUE, TRUE, 'Ativo', '11111111111', '81111111111', '1990-01-01', '12345')
        """
        
        cur.execute(sql)
        conn.commit()
        print("INSERT SUCESSO!")
        
    except Exception:
        with open("error_log.txt", "w") as f:
            traceback.print_exc(file=f)
        print("Erro gravado em error_log.txt")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    debug_insert()
