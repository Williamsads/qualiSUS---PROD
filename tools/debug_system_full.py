
import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def debug_everything():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        print("--- ESPECIALIDADES ---")
        cur.execute("SELECT * FROM especialidades LIMIT 10")
        for row in cur.fetchall():
            print(row)
            
        print("\n--- TRABALHADOR (WILLIAMS) ---")
        cur.execute("SELECT id, nome_completo, acolhimento_realizado FROM trabalhadores WHERE cpf = '12973552451'")
        worker = cur.fetchone()
        print(worker)
        
        if worker:
            print("\n--- AGENDAMENTOS DO TRABALHADOR ---")
            cur.execute("SELECT id, especialidade, status, data_consulta FROM agendamento_exames WHERE trabalhador_id = %s", (worker['id'],))
            for ag in cur.fetchall():
                print(ag)
                
        print("\n--- VERIFICAÇÃO DE TRIGGER ---")
        # Check if function exists
        cur.execute("SELECT routine_name FROM information_schema.routines WHERE routine_name = 'fn_atualizar_flag_acolhimento'")
        print(f"Function fn_atualizar_flag_acolhimento: {cur.fetchone()}")
        
        # Check if trigger exists
        cur.execute("SELECT trigger_name FROM information_schema.triggers WHERE trigger_name = 'trg_liberacao_acolhimento'")
        print(f"Trigger trg_liberacao_acolhimento: {cur.fetchone()}")

    except Exception as e:
        print(f"Erro: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    debug_everything()
