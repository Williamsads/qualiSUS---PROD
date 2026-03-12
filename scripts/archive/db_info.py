import psycopg2
from psycopg2.extras import RealDictCursor

try:
    conn = psycopg2.connect(host='10.24.59.104', user='qualisus', password='h5eXAx59gJ3h84Xa', database='qualisus')
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'agendamento_exames'")
    cols = [r['column_name'] for r in cur.fetchall()]
    print("Columns of agendamento_exames:", ",".join(cols))
    
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    tables = [r['tablename'] for r in cur.fetchall()]
    print("Tables:", ",".join(tables))
            
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
