
import psycopg2
from psycopg2.extras import RealDictCursor

def check_worker_in_funcionarios(name):
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM funcionarios WHERE nome ILIKE %s", (f"%{name}%",))
        rows = cursor.fetchall()
        print(f"Workers in funcionarios matching {name}:")
        for row in rows:
            print(row)
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_worker_in_funcionarios("ABDI JOAQUIM")
