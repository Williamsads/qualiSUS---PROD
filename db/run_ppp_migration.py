import psycopg2
import os

def run_migration():
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cursor = conn.cursor()
        
        print("Listing all tables in all schemas:")
        cursor.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog')")
        for t in cursor.fetchall():
            print(f"- {t[0]}.{t[1]}")
        
        # Check specifically for unidades*
        print("\nChecking for 'unidades' related tables:")
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'unidades%'")
        for t in cursor.fetchall():
            print(f"Found: {t[0]}")

        migration_path = os.path.join(os.path.dirname(__file__), 'migration_ppp.sql')
        with open(migration_path, 'r', encoding='utf-8') as f:
            sql = f.read()
            
        print(f"Executing migration from {migration_path}...")
        cursor.execute(sql)
        conn.commit()
        print("Migration executed successfully!")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_migration()
