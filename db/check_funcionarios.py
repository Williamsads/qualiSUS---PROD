
import psycopg2
from psycopg2.extras import RealDictCursor

def check_funcionarios_schema():
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM funcionarios LIMIT 1")
        row = cursor.fetchone()
        if row:
            print("Columns in funcionarios:")
            print(list(row.keys()))
        else:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'funcionarios'")
            cols = [r['column_name'] for r in cursor.fetchall()]
            print("Column list from information_schema:")
            print(cols)
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_funcionarios_schema()
