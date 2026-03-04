
import psycopg2

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def run_fix():
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        print("Corrigindo function para trigger (Case Insensitivity)...")
        cur.execute("""
            CREATE OR REPLACE FUNCTION fn_atualizar_flag_acolhimento()
            RETURNS trigger AS $$
            BEGIN
                -- Busca o tipo_fluxo ignorando maiúsculas/minúsculas
                IF (SELECT tipo_fluxo FROM especialidades WHERE LOWER(nome) = LOWER(NEW.especialidade)) = 'ACOLHIMENTO' 
                   AND NEW.status = 'Finalizado' THEN
                   
                    UPDATE trabalhadores
                    SET acolhimento_realizado = TRUE
                    WHERE id = NEW.trabalhador_id;
                    
                    RAISE NOTICE 'Flag de acolhimento liberada para trabalhador_id %', NEW.trabalhador_id;
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        print("Sincronizando flags para pacientes que já finalizaram acolhimento...")
        cur.execute("""
            UPDATE trabalhadores t
            SET acolhimento_realizado = TRUE
            WHERE EXISTS (
                SELECT 1 FROM agendamento_exames ae
                WHERE ae.trabalhador_id = t.id
                  AND LOWER(ae.especialidade) ILIKE '%acolhimento%'
                  AND ae.status = 'Finalizado'
            );
        """)
        
        conn.commit()
        print("Correção de banco concluída com sucesso!")
        
    except Exception as e:
        conn.rollback()
        print(f"Erro na correção: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    run_fix()
