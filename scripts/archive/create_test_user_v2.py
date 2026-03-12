import psycopg2
from werkzeug.security import generate_password_hash

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def criar_profissional_tste():
    conn = get_connection()
    cur = conn.cursor()
    
    email = "ana.souza@qualisus.com"
    senha_hash = generate_password_hash("123456")
    
    print(f"Tentando criar/atualizar: {email}")

    try:
        # Verifica se o usuario de login existe
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        user_row = cur.fetchone()
        
        if user_row:
            user_id = user_row[0]
            print(f"Usuário login encontrado ID {user_id}. Atualizando...")
            cur.execute("""
                UPDATE usuarios 
                SET senha = %s, tipo = 'Médico', nome = 'Dra. Ana Souza', ativo = TRUE
                WHERE id = %s
            """, (senha_hash, user_id))
        else:
            print("Criando usuário de login...")
            cur.execute("""
                INSERT INTO usuarios (nome, email, senha, tipo, ativo)
                VALUES ('Dra. Ana Souza', %s, %s, 'Médico', TRUE)
                RETURNING id
            """, (email, senha_hash))
            user_id = cur.fetchone()[0]

        # Verifica funcionario
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
                    situacao = 'Ativo'
                WHERE id = %s
            """, (func_id,))
        else:
            print("Criando funcionário...")
            # Tentativa com mais campos para evitar erro de NOT NULL
            cur.execute("""
                INSERT INTO funcionarios 
                (nome, email, especialidade, unidade_atendimento, ativo, atendimento, situacao, cpf, telefone)
                VALUES 
                ('Dra. Ana Souza', %s, 'Psicólogo', 'USF Centro', TRUE, TRUE, 'Ativo', '12345678900', '81999999999')
                RETURNING id
            """, (email,))
            func_id = cur.fetchone()[0]

        # Vínculo Especialidade
        cur.execute("SELECT id FROM especialidades WHERE nome = 'Psicólogo'")
        esp = cur.fetchone()
        if esp:
            cur.execute("""
                INSERT INTO funcionarios_especialidades (funcionario_id, especialidade_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (func_id, esp[0]))

        conn.commit()
        print("\n=== SUCESSO! ===")
        print(f"Login: {email}")
        print("Senha: 123456")
        print("================\n")
        
    except Exception as e:
        conn.rollback()
        print(f"Erro SQL: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    criar_profissional_tste()
