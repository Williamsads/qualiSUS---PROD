import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def check_mapping():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n--- Columns in 'usuarios' ---")
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'usuarios'")
    for row in cur.fetchall():
        print(row['column_name'])
        
    print("\n--- Columns in 'funcionarios' ---")
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'funcionarios'")
    for row in cur.fetchall():
        print(row['column_name'])
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_mapping()
