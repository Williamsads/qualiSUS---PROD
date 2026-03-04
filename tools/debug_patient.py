
import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def check_patient_status(cpf):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("SELECT id, nome_completo, acolhimento_realizado FROM trabalhadores WHERE cpf = %s", (cpf,))
        patient = cur.fetchone()
        
        if not patient:
            print("Paciente não encontrado.")
            return
            
        print(f"Paciente: {patient['nome_completo']}")
        print(f"Flag Acolhimento Realizado: {patient['acolhimento_realizado']}")
        
        cur.execute("""
            SELECT id, especialidade, status, data_consulta 
            FROM agendamento_exames 
            WHERE trabalhador_id = %s 
            ORDER BY data_consulta DESC
        """, (patient['id'],))
        agendamentos = cur.fetchall()
        
        print("\nAgendamentos:")
        for ag in agendamentos:
            print(f"- {ag['especialidade']} | {ag['status']} | {ag['data_consulta']}")
            
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    check_patient_status("12973552451")
