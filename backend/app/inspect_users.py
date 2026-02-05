import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def inspect_users():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'usuarios'")
    cols = cur.fetchall()
    print("Colunas da tabela 'usuarios':")
    for col in cols:
        print(f" - {col['column_name']} ({col['data_type']})")
    cur.close()
    conn.close()

if __name__ == "__main__":
    inspect_users()
