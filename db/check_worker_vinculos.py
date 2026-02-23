
import psycopg2
from psycopg2.extras import RealDictCursor

def check_worker_vinculos(name):
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT v.* 
            FROM vinculos_trabalhadores v 
            JOIN trabalhadores t ON v.trabalhador_id = t.id 
            WHERE t.nome_completo ILIKE %s
        """
        cursor.execute(query, (f"%{name}%",))
        rows = cursor.fetchall()
        print(f"Vinculos for {name}:")
        for row in rows:
            print(row)
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_worker_vinculos("ABDI JOAQUIM")
