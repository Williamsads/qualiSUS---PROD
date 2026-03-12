import psycopg2
import os

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def setup_db():
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        print("Criando tabela tratamentos...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tratamentos (
                id SERIAL PRIMARY KEY,
                trabalhador_id INTEGER REFERENCES trabalhadores(id),
                funcionario_id INTEGER REFERENCES funcionarios(id),
                data_inicio DATE,
                frequencia VARCHAR(50),
                data_ultima_consulta DATE,
                data_alta DATE,
                observacao_alta TEXT,
                status VARCHAR(20) DEFAULT 'Em tratamento',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Adicionar coluna 'bloqueado_psico' na tabela trabalhadores se não existir
        # Ou criar uma tabela de bloqueios. O usuário disse: "o sistema deve registrar que o paciente não pode agendar... sem passar por um novo acolhimento"
        # Isso parece resetar o ciclo. 
        # Vou assumir que o bloqueio será verificado na hora do agendamento olhando se existe tratamento com status 'Alta' e sem novo acolhimento.
        
        conn.commit()
        print("Tabela tratamentos criada com sucesso!")
        
    except Exception as e:
        conn.rollback()
        print(f"Erro ao criar tabela: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    setup_db()
