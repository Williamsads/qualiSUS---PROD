from backend.app.app import get_connection

def debug_horarios():
    conn = get_connection()
    cur = conn.cursor()
    
    print("--- Sample data from horarios_funcionarios ---")
    cur.execute("SELECT id, funcionario_id, horario, dia_semana FROM horarios_funcionarios LIMIT 10")
    for row in cur.fetchall():
        print(row)
        
    print("\n--- Checking for potential 'visual' duplicates ---")
    cur.execute("""
        SELECT funcionario_id, horario, dia_semana, COUNT(*)
        FROM horarios_funcionarios
        GROUP BY funcionario_id, horario, dia_semana
        HAVING COUNT(*) > 1
    """)
    rows = cur.fetchall()
    if rows:
        print("Found duplicates!")
        for r in rows:
            print(r)
    else:
        print("No duplicates found by query.")
        
    conn.close()

if __name__ == "__main__":
    debug_horarios()
