from backend.app.app import get_connection

def check_columns():
    conn = get_connection()
    cur = conn.cursor()
    
    tables = ['desfechos_clinicos', 'ciclo_cuidado', 'paciente_tratamento']
    for table in tables:
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'")
        columns = [row[0] for row in cur.fetchall()]
        print(f"{table}: {','.join(columns)}")
    
    conn.close()

if __name__ == "__main__":
    check_columns()
