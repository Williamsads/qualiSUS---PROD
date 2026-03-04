from backend.app.app import get_connection

def check_horarios_schema():
    conn = get_connection()
    cur = conn.cursor()
    
    print("--- Columns for horarios_funcionarios ---")
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'horarios_funcionarios'")
    for row in cur.fetchall():
        print(row[0])
        
    print("\n--- Constraints for horarios_funcionarios ---")
    cur.execute("SELECT conname FROM pg_constraint WHERE conrelid = 'horarios_funcionarios'::regclass")
    for row in cur.fetchall():
        print(row[0])
        
    conn.close()

if __name__ == "__main__":
    check_horarios_schema()
