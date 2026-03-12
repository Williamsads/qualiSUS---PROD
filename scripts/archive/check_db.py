import psycopg2

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def check():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    print("Tables:", [r[0] for r in cur.fetchall()])
    
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'funcionarios'")
    print("Columns in funcionarios:", [r[0] for r in cur.fetchall()])
    
    # Check if a many-to-many table for professional specialties exists
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'funcionarios_especialidades'")
    print("Bridge table exists:", cur.fetchone() is not None)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check()
