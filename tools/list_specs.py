import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def list_specs():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, nome FROM especialidades ORDER BY nome")
    specs = cur.fetchall()
    for s in specs:
        print(f"ID: {s['id']}, Name: {s['nome']}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    list_specs()
