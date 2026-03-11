import os
import sys
import psycopg2
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
load_dotenv(os.path.join(os.path.dirname(__file__), '../backend/.env'))

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        database=os.getenv("DB_NAME", ""),
        user=os.getenv("DB_USER", ""),
        password=os.getenv("DB_PASSWORD", "")
    )

def main():
    print("Mapeando profissões perdidas e recriando vínculos de especialidades...")
    try:
        conn = get_connection()
        conn.autocommit = False
        cur = conn.cursor()
        
        # 1. Pega os médicos que hoje não estão em `funcionarios_especialidades` 
        # e nem tem `especialidade_id` na tabela `funcionarios`
        cur.execute("""
            SELECT id, nome, especialidade 
            FROM funcionarios 
            WHERE id NOT IN (SELECT funcionario_id FROM funcionarios_especialidades)
              AND (especialidade_id IS NULL OR especialidade_id = 0)
        """)
        medicos_perdidos = cur.fetchall()
        
        print(f"Total de funcionários perdidos encontrados: {len(medicos_perdidos)}")
        
        processados = 0
        for m_id, m_nome, m_prof in medicos_perdidos:
            if not m_prof:
                continue
                
            # Limpa o texto da profissao pra padronizar
            profissao_limpa = m_prof.strip().title()
            
            # Checa se já não criamos essa especialidade nas iterações anteriores (ou se já havia)
            cur.execute("SELECT id FROM especialidades WHERE nome ILIKE %s LIMIT 1", (f"%{profissao_limpa}%",))
            row = cur.fetchone()
            
            if row:
                esp_id = row[0]
            else:
                # Se não existe essa vaga de fato na tabela official, nós a cadastraremos
                print(f" [+] Criando nova especialidade base oficial no banco: {profissao_limpa}")
                cur.execute(
                    "INSERT INTO especialidades (nome, descricao, visivel, exige_acolhimento_previo) VALUES (%s, %s, true, false) RETURNING id",
                    (profissao_limpa, m_prof)
                )
                esp_id = cur.fetchone()[0]
                
            # Cria o vínculo na tabela N:N
            print(f"   -> Vinculando {m_nome} à especialidade (ID:{esp_id})")
            cur.execute("INSERT INTO funcionarios_especialidades (funcionario_id, especialidade_id) VALUES (%s, %s)", (m_id, esp_id))
            
            # Atualiza o Atalho Especialidade_id na própria Tabela Funcionário (backup da informação)
            cur.execute("UPDATE funcionarios SET especialidade_id = %s WHERE id = %s", (esp_id, m_id))
            
            processados += 1
            
        conn.commit()
        print(f"SUCESSO! {processados} registros de médicos e especialidades foram restabelecidos e re-pareados de volta à base!")
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"Erro: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    main()
