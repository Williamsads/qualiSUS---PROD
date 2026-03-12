import psycopg2

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def setup_multi_specialty():
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Create bridge table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS funcionarios_especialidades (
                funcionario_id INTEGER REFERENCES funcionarios(id) ON DELETE CASCADE,
                especialidade_id INTEGER REFERENCES especialidades(id) ON DELETE CASCADE,
                PRIMARY KEY (funcionario_id, especialidade_id)
            )
        """)
        print("Table 'funcionarios_especialidades' created.")
        
        # Migrate existing data
        cur.execute("SELECT id, especialidade_id FROM funcionarios WHERE especialidade_id IS NOT NULL")
        rows = cur.fetchall()
        for f_id, e_id in rows:
            cur.execute("""
                INSERT INTO funcionarios_especialidades (funcionario_id, especialidade_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (f_id, e_id))
        print(f"Migrated {len(rows)} specialties.")
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    setup_multi_specialty()
