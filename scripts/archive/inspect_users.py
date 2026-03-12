
import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def inspect_users():
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM usuarios LIMIT 1")
        user = cur.fetchone()
        
        if user:
            print("Columns in 'usuarios' table:")
            for key in user.keys():
                print(f"- {key}: {user[key]}")
        else:
            print("No users found, but table likely exists.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_users()
