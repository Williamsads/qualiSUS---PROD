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
    
    try:
        # 1. Inserir/Atualizar na tabela FUNCIONARIOS (Perfil Profissional)
        cur.execute("SELECT id FROM funcionarios WHERE email = %s", (email,))
        func = cur.fetchone()
        
        if func:
            print(f"Profissional {email} já existe (ID: {func[0]}). Atualizando dados...")
            cur.execute("""
                UPDATE funcionarios 
                SET nome = 'Dra. Ana Souza', 
                    especialidade = 'Psicólogo',
                    unidade_atendimento = 'USF Centro',
                    ativo = TRUE,
                    atendimento = TRUE,
                    situacao = 'Ativo'
                WHERE id = %s
            """, (func[0],))
            funcionario_id = func[0]
        else:
            print(f"Criando nova profissional {email}...")
            cur.execute("""
                INSERT INTO funcionarios (nome, email, especialidade, unidade_atendimento, ativo, atendimento, situacao)
                VALUES ('Dra. Ana Souza', %s, 'Psicólogo', 'USF Centro', TRUE, TRUE, 'Ativo')
                RETURNING id
            """, (email,))
            funcionario_id = cur.fetchone()[0]
            
        # 2. Garantir Especialidade na tabela de relacionamento (se houver essa modelagem)
        # Verificando se existe especialidade 'Psicólogo'
        cur.execute("SELECT id FROM especialidades WHERE nome = 'Psicólogo'")
        esp = cur.fetchone()
        if esp:
            esp_id = esp[0]
            # Vincula
            cur.execute("""
                INSERT INTO funcionarios_especialidades (funcionario_id, especialidade_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (funcionario_id, esp_id))
            
        # 3. Inserir/Atualizar na tabela USUARIOS (Login)
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        user = cur.fetchone()
        
        if user:
            print("Atualizando senha do usuário de login...")
            cur.execute("UPDATE usuarios SET senha = %s, tipo = 'Médico', nome = 'Dra. Ana Souza' WHERE email = %s", (senha_hash, email))
        else:
            print("Criando usuário de login...")
            cur.execute("""
                INSERT INTO usuarios (nome, email, senha, tipo)
                VALUES ('Dra. Ana Souza', %s, %s, 'Médico')
            """, (email, senha_hash))
            
        conn.commit()
        print("\n=== SUCESSO! ===")
        print(f"Login: {email}")
        print("Senha: 123456")
        print("================\n")
        
    except Exception as e:
        conn.rollback()
        print(f"Erro: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    criar_profissional_tste()
