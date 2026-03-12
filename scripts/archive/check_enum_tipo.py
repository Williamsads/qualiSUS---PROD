import psycopg2

def check_enum():
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cur = conn.cursor()
        
        # Verificar se tipo é ENUM
        print("Verificando tipo da coluna 'tipo' na tabela usuarios...")
        cur.execute("""
            SELECT data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'usuarios' AND column_name = 'tipo'
        """)
        row = cur.fetchone()
        print(f"Data Type: {row[0]}")
        print(f"UDT Name: {row[1]}")
        
        # Se for USER-DEFINED (ENUM), listar valores
        if row[0] == 'USER-DEFINED':
            print(f"\nListando valores do ENUM '{row[1]}':")
            cur.execute("""
                SELECT enumlabel 
                FROM pg_enum 
                JOIN pg_type ON pg_enum.enumtypid = pg_type.oid 
                WHERE pg_type.typname = %s
                ORDER BY enumsortorder
            """, (row[1],))
            
            enum_values = cur.fetchall()
            for val in enum_values:
                print(f"  - {val[0]}")
        else:
            print("\nNao e ENUM. Valores existentes na tabela:")
            cur.execute("SELECT DISTINCT tipo FROM usuarios")
            for val in cur.fetchall():
                print(f"  - {val[0]}")
        
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()
        
if __name__ == "__main__":
    check_enum()
