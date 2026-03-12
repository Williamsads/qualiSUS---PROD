import psycopg2

def update_ana_robust():
    conn = None
    try:
        conn = psycopg2.connect(
            host="10.24.59.104",
            user="qualisus",
            password="h5eXAx59gJ3h84Xa",
            database="qualisus"
        )
        cur = conn.cursor()
        
        email = "ana.souza.final@qualisus.com"
        
        # Verificar antes
        print("ANTES DO UPDATE:")
        cur.execute("SELECT tipo FROM usuarios WHERE email = %s", (email,))
        row = cur.fetchone()
        print(f"Tipo atual: {row[0] if row else 'NAO ENCONTRADO'}")
        
        # Fazer UPDATE
        print("\nExecutando UPDATE...")
        cur.execute("UPDATE usuarios SET tipo = %s WHERE email = %s", ('medico', email))
        
        # Verificar quantas linhas foram afetadas
        print(f"Linhas afetadas: {cur.rowcount}")
        
        # COMMIT
        conn.commit()
        print("COMMIT executado!")
        
        # Verificar depois
        print("\nDEPOIS DO UPDATE:")
        cur.execute("SELECT tipo FROM usuarios WHERE email = %s", (email,))
        row = cur.fetchone()
        print(f"Tipo atualizado: {row[0] if row else 'NAO ENCONTRADO'}")
        
        print("\n=== SUCESSO ===")
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
        
if __name__ == "__main__":
    update_ana_robust()
