
import psycopg2
from psycopg2.extras import RealDictCursor

def check():
    conn = psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("--- PATIENTS ---")
    cur.execute("SELECT id, nome_completo, acolhimento_realizado FROM trabalhadores WHERE nome_completo ILIKE '%Williams%Americo%'")
    patients = cur.fetchall()
    for p in patients:
        print(p)
        
    print("\n--- SPECIALTIES ---")
    cur.execute("SELECT id, nome, exige_acolhimento_previo, tipo_fluxo FROM especialidades WHERE nome ILIKE '%Psic%' OR nome ILIKE '%Acolhimento%'")
    for s in cur.fetchall():
        print(s)
        
    print("\n--- RECENT APPOINTMENTS FOR WILLIAMS ---")
    if patients:
        cur.execute("SELECT id, especialidade, status, data_consulta, horario FROM agendamento_exames WHERE trabalhador_id = %s ORDER BY data_consulta DESC LIMIT 5", (patients[0]['id'],))
        for a in cur.fetchall():
            print(a)
            
    cur.close()
    conn.close()

if __name__ == "__main__":
    check()
