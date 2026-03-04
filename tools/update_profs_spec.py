import psycopg2

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def update_profs():
    conn = get_connection()
    cur = conn.cursor()
    # Update the text column 'especialidade' for all professionals with specialty_id 5
    cur.execute("UPDATE funcionarios SET especialidade = 'Terapia Ocupacional' WHERE especialidade_id = 5")
    row_count = cur.rowcount
    conn.commit()
    print(f"Updated {row_count} professionals with new specialty name.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    update_profs()
