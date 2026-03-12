import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def search_anywhere(query_str):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    print(f"Searching anywhere for: {query_str}")
    
    cur.execute("SELECT * FROM vinculos_trabalhadores WHERE numero_funcional LIKE %s", (f"%{query_str}%",))
    vinc = cur.fetchall()
    print(f"FOUND VINCULOS: {len(vinc)}")
    for v in vinc:
        print(v)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    search_anywhere("1338234")
