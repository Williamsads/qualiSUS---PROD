from backend.app.app import get_connection

def fix_horarios_duplicates():
    conn = get_connection()
    cur = conn.cursor()
    
    print("--- Cleaning up duplicates in horarios_funcionarios ---")
    try:
        # Keep only the row with the smallest ID for each (funcionario_id, horario, dia_semana)
        cur.execute("""
            DELETE FROM horarios_funcionarios a
            WHERE a.id > (
                SELECT MIN(b.id) FROM horarios_funcionarios b
                WHERE a.funcionario_id = b.funcionario_id
                  AND a.horario = b.horario
                  AND a.dia_semana = b.dia_semana
            )
        """)
        print(f"Duplicates removed: {cur.rowcount}")
        
        print("--- Adding unique constraint (funcionario_id, horario, dia_semana) ---")
        cur.execute("""
            ALTER TABLE horarios_funcionarios 
            ADD CONSTRAINT idx_horario_unique UNIQUE (funcionario_id, horario, dia_semana)
        """)
        conn.commit()
        print("Constraint added successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        
    conn.close()

if __name__ == "__main__":
    fix_horarios_duplicates()
