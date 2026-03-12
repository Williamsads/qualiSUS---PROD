import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

if __name__ == "__main__":
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT t.nome_completo, vt.numero_funcional FROM trabalhadores t JOIN vinculos_trabalhadores vt ON vt.trabalhador_id = t.id WHERE vt.numero_funcional LIKE '%38234%'")
    rows = cur.fetchall()
    for r in rows:
        print(f"NOME: {r['nome_completo']} | MATRICULA: {r['numero_funcional']}")
    cur.close()
    conn.close()
