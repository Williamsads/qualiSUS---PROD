
import psycopg2
from psycopg2.extras import RealDictCursor

def check_schema():
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM trabalhadores LIMIT 1")
        row = cursor.fetchone()
        if row:
            print("Columns in trabalhadores:")
            print(list(row.keys()))
        else:
            print("No data in trabalhadores table.")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()
