
import psycopg2

def check_trabalhadores():
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cursor = conn.cursor()
        
        print("Trabalhadores available:")
        cursor.execute("SELECT id, nome_completo, cpf FROM trabalhadores LIMIT 10")
        rows = cursor.fetchall()
        for r in rows:
            print(f"ID: {r[0]}, Nome: {r[1]}, CPF: {r[2]}")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_trabalhadores()
