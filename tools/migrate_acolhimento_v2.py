
import psycopg2

def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

def run_migration():
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        print("Adicionando colunas em especialidades...")
        cur.execute("""
            ALTER TABLE especialidades 
            ADD COLUMN IF NOT EXISTS tipo_fluxo VARCHAR(20) DEFAULT 'CONSULTA',
            ADD COLUMN IF NOT EXISTS exige_acolhimento_previo BOOLEAN DEFAULT FALSE;
        """)
        
        print("Adicionando coluna em trabalhadores...")
        cur.execute("""
            ALTER TABLE trabalhadores 
            ADD COLUMN IF NOT EXISTS acolhimento_realizado BOOLEAN DEFAULT FALSE;
        """)
        
        print("Configurando especialidades iniciais...")
        cur.execute("""
            UPDATE especialidades SET tipo_fluxo = 'ACOLHIMENTO' WHERE nome ILIKE '%Acolhimento%';
            UPDATE especialidades SET exige_acolhimento_previo = TRUE WHERE nome IN ('Psicologia', 'Psiquiatria');
        """)
        
        print("Criando function para trigger...")
        cur.execute("""
            CREATE OR REPLACE FUNCTION fn_atualizar_flag_acolhimento()
            RETURNS trigger AS $$
            BEGIN
                -- Verifica se o agendamento finalizado era do tipo ACOLHIMENTO
                -- Nota: estamos usando o ID da especialidade se disponível, ou o nome se não.
                -- No agendamento_exames, temos especialidade (nome) e vinculo_id.
                -- Vamos buscar o tipo_fluxo baseado no nome da especialidade registrado no agendamento.
                
                IF (SELECT tipo_fluxo FROM especialidades WHERE nome = NEW.especialidade) = 'ACOLHIMENTO' 
                   AND NEW.status = 'Finalizado' THEN
                   
                    UPDATE trabalhadores
                    SET acolhimento_realizado = TRUE
                    WHERE id = NEW.trabalhador_id;
                    
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        print("Criando trigger...")
        cur.execute("DROP TRIGGER IF EXISTS trg_liberacao_acolhimento ON agendamento_exames;")
        cur.execute("""
            CREATE TRIGGER trg_liberacao_acolhimento
            AFTER UPDATE OF status ON agendamento_exames
            FOR EACH ROW EXECUTE FUNCTION fn_atualizar_flag_acolhimento();
        """)
        
        conn.commit()
        print("Migração concluída com sucesso!")
        
    except Exception as e:
        conn.rollback()
        print(f"Erro na migração: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    run_migration()
