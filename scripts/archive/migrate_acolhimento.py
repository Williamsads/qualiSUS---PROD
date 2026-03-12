import psycopg2

try:
    conn = psycopg2.connect(host='10.24.59.104', user='qualisus', password='h5eXAx59gJ3h84Xa', database='qualisus')
    cur = conn.cursor()
    
    # 1. Add validado_para_psico to agendamento_exames
    print("Adding validado_para_psico column...")
    cur.execute("ALTER TABLE agendamento_exames ADD COLUMN IF NOT EXISTS validado_para_psico BOOLEAN DEFAULT FALSE")
    
    # 2. Create ciclo_cuidado table
    print("Creating ciclo_cuidado table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ciclo_cuidado (
            id SERIAL PRIMARY KEY,
            trabalhador_id INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'ATIVO',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_trabalhador FOREIGN KEY (trabalhador_id) REFERENCES trabalhadores(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    print("Success!")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
