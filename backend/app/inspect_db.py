import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def inspect_admissions():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\nAdmissions this month:")
    cur.execute("SELECT COUNT(*) FROM vinculos_trabalhadores WHERE data_admissao >= date_trunc('month', CURRENT_DATE)")
    print(f"This month: {cur.fetchone()['count']}")
    
    print("\nAdmissions last month:")
    cur.execute("SELECT COUNT(*) FROM vinculos_trabalhadores WHERE data_admissao >= date_trunc('month', CURRENT_DATE - interval '1 month') AND data_admissao < date_trunc('month', CURRENT_DATE)")
    print(f"Last month: {cur.fetchone()['count']}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    inspect_admissions()
