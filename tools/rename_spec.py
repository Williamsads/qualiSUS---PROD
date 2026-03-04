import psycopg2

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def rename_spec():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE especialidades SET nome = 'Terapia Ocupacional' WHERE id = 5")
    conn.commit()
    print("Specialty renamed to 'Terapia Ocupacional'")
    cur.close()
    conn.close()

if __name__ == "__main__":
    rename_spec()
