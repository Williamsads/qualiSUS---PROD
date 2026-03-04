
import psycopg2

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def update_rules():
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        print("Atualizando regras de especialidades...")
        
        # Define quem exige acolhimento
        cur.execute("""
            UPDATE especialidades 
            SET exige_acolhimento_previo = TRUE 
            WHERE nome ILIKE '%Psic%' 
               OR nome ILIKE '%Psiq%'
        """)
        print(f"Especialidades com bloqueio: {cur.rowcount}")

        # Define quem é acolhimento
        cur.execute("""
            UPDATE especialidades 
            SET tipo_fluxo = 'ACOLHIMENTO' 
            WHERE nome ILIKE '%Acolhimento%'
        """)
        print(f"Especialidades de fluxo Acolhimento: {cur.rowcount}")
        
        # Garante que as outras são CONSULTA
        cur.execute("""
            UPDATE especialidades 
            SET tipo_fluxo = 'CONSULTA' 
            WHERE tipo_fluxo IS NULL
        """)
        
        conn.commit()
        print("Sucesso!")
    except Exception as e:
        conn.rollback()
        print(f"Erro: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    update_rules()
