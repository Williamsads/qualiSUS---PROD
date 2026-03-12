import psycopg2
from werkzeug.security import generate_password_hash

def criar_profissional_tste_final():
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cur = conn.cursor()
        
        email = "ana.souza@qualisus.com"
        senha = "123" # Senha simples
        senha_hash = generate_password_hash(senha)
        
        print(f"Tentando criar/atualizar: {email}")

        # 1. USUARIOS (Login)
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        user_row = cur.fetchone()
        
        if user_row:
            print(f"Usuário login encontrado ID {user_row[0]}. Atualizando...")
            cur.execute("UPDATE usuarios SET senha = %s, tipo = 'Médico', nome = 'Dra. Ana Souza', ativo = TRUE WHERE id = %s", (senha_hash, user_row[0]))
        else:
            print("Criando usuário de login...")
            cur.execute("INSERT INTO usuarios (nome, email, senha, tipo, ativo) VALUES ('Dra. Ana Souza', %s, %s, 'Médico', TRUE)", (email, senha_hash))

        # 2. FUNCIONARIOS (Perfil Profissional)
        cur.execute("SELECT id FROM funcionarios WHERE email = %s", (email,))
        func_row = cur.fetchone()
        
        if func_row:
             func_id = func_row[0]
             print(f"Funcionário encontrado ID {func_id}. Atualizando...")
             cur.execute("""
                UPDATE funcionarios 
                SET nome = 'Dra. Ana Souza', 
                    especialidade = 'Psicólogo',
                    unidade_atendimento = 'USF Centro',
                    ativo = TRUE,
                    atendimento = TRUE,
                    situacao = 'Ativo',
                    data_nascimento = '1985-05-15',
                    telefone = '81999999999',
                    cpf = '12345678900',
                    num_func_num_vinc = 'FUNC123'
                WHERE id = %s
            """, (func_id,))
        else:
            print("Criando funcionário...")
            cur.execute("""
                INSERT INTO funcionarios 
                (nome, email, especialidade, unidade_atendimento, ativo, atendimento, situacao, cpf, telefone, data_nascimento, num_func_num_vinc)
                VALUES 
                ('Dra. Ana Souza', %s, 'Psicólogo', 'USF Centro', TRUE, TRUE, 'Ativo', '12345678900', '81999999999', '1985-05-15', 'FUNC123')
                RETURNING id
            """, (email,))
            func_id = cur.fetchone()[0]

        # 3. Vínculo Especialidade
        cur.execute("SELECT id FROM especialidades WHERE nome = 'Psicólogo'")
        esp = cur.fetchone()
        if esp:
            cur.execute("""
                INSERT INTO funcionarios_especialidades (funcionario_id, especialidade_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (func_id, esp[0]))

        conn.commit()
        print("\n=== SUCESSO TOTAL! ===")
        print(f"Login: {email}")
        print(f"Senha: {senha}")
        print("======================\n")
        
    except Exception as e:
        conn.rollback()
        print(f"ERRO CRÍTICO: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    criar_profissional_tste_final()
