import psycopg2

def list_tables_safe():
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [r[0] for r in cur.fetchall()]
        print(f"All Tables: {tables}")
    except Exception as e:
        print(e)
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    list_tables_safe()
