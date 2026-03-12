import psycopg2

def add_medico_to_enum():
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cur = conn.cursor()
        
        print("Adicionando 'medico' ao ENUM tipo_usuario...")
        
        # ALTER TYPE para adicionar novo valor
        cur.execute("ALTER TYPE tipo_usuario ADD VALUE IF NOT EXISTS 'medico'")
        conn.commit()
        
        print("SUCESSO! Valor 'medico' adicionado ao ENUM.")
        
        # Verificar
        print("\nValores atuais do ENUM:")
        cur.execute("""
            SELECT enumlabel 
            FROM pg_enum 
            JOIN pg_type ON pg_enum.enumtypid = pg_type.oid 
            WHERE pg_type.typname = 'tipo_usuario'
            ORDER BY enumsortorder
        """)
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
    add_medico_to_enum()
