from backend.app.app import get_connection

def check_columns():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'agendamento_exames'")
    columns = [row[0] for row in cur.fetchall()]
    print(f"AE: {','.join(columns)}")
    
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'paciente_tratamento'")
    columns_pt = [row[0] for row in cur.fetchall()]
    print(f"PT: {','.join(columns_pt)}")
    
    conn.close()

if __name__ == "__main__":
    check_columns()
