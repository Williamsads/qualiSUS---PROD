import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def inspect_schema():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n--- SCHEMA: paciente_tratamento ---")
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'paciente_tratamento'")
    for row in cur.fetchall():
        print(row)
        
    print("\n--- SCHEMA: ciclo_cuidado ---")
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'ciclo_cuidado'")
    for row in cur.fetchall():
        print(row)

    cur.close()
    conn.close()

if __name__ == "__main__":
    inspect_schema()
