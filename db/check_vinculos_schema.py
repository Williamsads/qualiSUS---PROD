
import psycopg2
from psycopg2.extras import RealDictCursor

def check_vinculos_schema():
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM vinculos_trabalhadores LIMIT 1")
        row = cursor.fetchone()
        if row:
            print("Columns in vinculos_trabalhadores:")
            print(list(row.keys()))
        else:
            print("No data in vinculos_trabalhadores table.")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_vinculos_schema()
