import psycopg2
from werkzeug.security import generate_password_hash

def criar_login_final():
    conn = None
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
        
        print(f"--- Criando USUÁRIO (Login) ---")
        
        # 1. USUARIOS
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        user_row = cur.fetchone()
        
        if user_row:
            user_id = user_row[0]
            print(f"Usuário login encontrado (ID {user_id}). Atualizando senha...")
            cur.execute("""
                UPDATE usuarios 
                SET senha = %s, tipo = 'Médico', nome = 'Dra. Ana Souza', ativo = TRUE 
                WHERE id = %s
            """, (senha_hash, user_id))
        else:
            print("Criando novo usuário de login...")
            cur.execute("""
                INSERT INTO usuarios (nome, email, senha, tipo, ativo) 
                VALUES ('Dra. Ana Souza', %s, %s, 'Médico', TRUE)
            """, (email, senha_hash))

        print(f"--- Criando FUNCIONÁRIO (Perfil) ---")

        # 2. FUNCIONARIOS
        cur.execute("SELECT id FROM funcionarios WHERE email = %s", (email,))
        func_row = cur.fetchone()
        
        if func_row:
             func_id = func_row[0]
             print(f"Funcionário encontrado (ID {func_id}). Atualizando dados...")
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
            print("Inserindo novo funcionário...")
            cur.execute("""
                INSERT INTO funcionarios 
                (nome, email, especialidade, unidade_atendimento, ativo, atendimento, situacao, cpf, telefone, data_nascimento, num_func_num_vinc)
                VALUES 
                ('Dra. Ana Souza', %s, 'Psicólogo', 'USF Centro', TRUE, TRUE, 'Ativo', '12345678900', '81999999999', '1985-05-15', 'FUNC123')
                RETURNING id
            """, (email,))
            func_id = cur.fetchone()[0]

        # 3. Vínculo Especialidade
        print("--- Vinculando Especialidade ---")
        cur.execute("SELECT id FROM especialidades WHERE nome = 'Psicólogo'")
        esp = cur.fetchone()
        if esp:
            cur.execute("""
                INSERT INTO funcionarios_especialidades (funcionario_id, especialidade_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (func_id, esp[0]))

        conn.commit()
        print("\n==================================")
        print(" SUCESSO! Usuário criado/atualizado.")
        print(f" Email: {email}")
        print(f" Senha: {senha}")
        print("==================================\n")
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERRO: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    criar_login_final()
