import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def check_visibility():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("SELECT id, nome, visivel, icone FROM especialidades WHERE id = 5")
    spec = cur.fetchone()
    print(f"Specialty ID 5: {spec}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_visibility()
