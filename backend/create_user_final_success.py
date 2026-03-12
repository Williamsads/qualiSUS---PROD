import psycopg2
from werkzeug.security import generate_password_hash

def create_success():
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cur = conn.cursor()
        
        email = "ana.souza.final@qualisus.com"
        senha = "123"
        senha_hash = generate_password_hash(senha)
        
        print("1. Criando login (tabela usuarios)...")
        # INSERT com conflito ignorado (se ja existe, atualiza senha)
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        row = cur.fetchone()
        if row:
            print("Usuario ja existe. Atualizando senha...")
            cur.execute("UPDATE usuarios SET senha=%s, tipo='usuario', ativo=TRUE WHERE id=%s", (senha_hash, row[0]))
        else:
            print("Usuario novo...")
            cur.execute("INSERT INTO usuarios (nome, email, senha, tipo, ativo) VALUES ('Dra Ana Final', %s, %s, 'usuario', TRUE)", (email, senha_hash))
            
        print("2. Criando perfil profissional (tabela funcionarios)...")
        cur.execute("SELECT id FROM funcionarios WHERE email = %s", (email,))
        row = cur.fetchone()
        if row:
            func_id = row[0]
            print("Funcionario ja existe. Atualizando...")
            cur.execute("""
                UPDATE funcionarios 
                SET nome='Dra Ana Final', especialidade='Psicólogo', unidade_atendimento='USF Centro', 
                    ativo=TRUE, atendimento=TRUE, situacao='Ativo', 
                    cpf='77777777777', telefone='81777777777', data_nascimento='1980-01-01', num_func_num_vinc='FUNC777'
                WHERE id=%s
            """, (func_id,))
        else:
            print("Funcionario novo...")
            cur.execute("""
                INSERT INTO funcionarios 
                (nome, email, especialidade, unidade_atendimento, ativo, atendimento, situacao, cpf, telefone, data_nascimento, num_func_num_vinc)
                VALUES 
                ('Dra Ana Final', %s, 'Psicólogo', 'USF Centro', TRUE, TRUE, 'Ativo', '77777777777', '81777777777', '1980-01-01', 'FUNC777')
                RETURNING id
            """, (email,))
            func_id = cur.fetchone()[0]

        print("3. Vinculando Especialidade...")
        cur.execute("SELECT id FROM especialidades WHERE nome LIKE 'Psic%' LIMIT 1")
        esp = cur.fetchone()
        if esp:
            cur.execute("INSERT INTO funcionarios_especialidades (funcionario_id, especialidade_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (func_id, esp[0]))
            
        conn.commit()
        print("\n==================================")
        print(" SUCESSO! Login criado.")
        print(f" Email: {email}")
        print(f" Senha: {senha}")
        print("==================================\n")
        
    except Exception as e:
        conn.rollback()
        print(f"ERRO: {e}")
    finally:
        if 'conn' in locals(): conn.close()
        
if __name__ == "__main__":
    create_success()
