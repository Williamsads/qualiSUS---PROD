import psycopg2
from psycopg2.extras import RealDictCursor

try:
    conn = psycopg2.connect(host='10.24.59.104', user='qualisus', password='h5eXAx59gJ3h84Xa', database='qualisus')
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Check columns of agendamento_exames
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'agendamento_exames'")
    columns = cur.fetchall()
    print("Columns of agendamento_exames:")
    for col in columns:
        print(f"  {col['column_name']} ({col['data_type']})")
        
    # Check if ciclo_cuidado exists
    cur.execute("SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'ciclo_cuidado')")
    exists = cur.fetchone()['exists']
    print(f"\nTable 'ciclo_cuidado' exists: {exists}")
    
    if exists:
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'ciclo_cuidado'")
        print("Columns of ciclo_cuidado:")
        for col in cur.fetchall():
            print(f"  {col['column_name']} ({col['data_type']})")
            
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
