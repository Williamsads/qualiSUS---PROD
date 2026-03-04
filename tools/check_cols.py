
import psycopg2

def check_columns():
    conn = psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )
    cur = conn.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'especialidades'")
    cols = [c[0] for c in cur.fetchall()]
    print("Columns in 'especialidades':", cols)
    
    cur.execute("SELECT * FROM especialidades LIMIT 1")
    row = cur.fetchone()
    print("Sample row:", row)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_columns()
