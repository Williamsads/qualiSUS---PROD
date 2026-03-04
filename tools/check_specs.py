import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

conn = get_connection()
cur = conn.cursor(cursor_factory=RealDictCursor)
cur.execute("SELECT nome FROM especialidades ORDER BY nome")
rows = cur.fetchall()
for row in rows:
    print(row['nome'])
cur.close()
conn.close()
