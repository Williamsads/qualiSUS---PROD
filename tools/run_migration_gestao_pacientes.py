"""
Script de Migração: Módulo Gestão de Pacientes
Executa a criação da tabela paciente_tratamento e migração de dados existentes.
Uso: python run_migration_gestao_pacientes.py
"""
import psycopg2

conn = psycopg2.connect(
    host="10.24.59.104",
    user="qualisus",
    password="h5eXAx59gJ3h84Xa",
    database="qualisus"
)
cur = conn.cursor()

print("🚀 Iniciando migração: Módulo Gestão de Pacientes...")

try:
    # ─── 1. Criar tabela paciente_tratamento ───────────────────────────
    print("   → Criando tabela paciente_tratamento...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS paciente_tratamento (
            id                      SERIAL PRIMARY KEY,
            ciclo_id                INTEGER NOT NULL REFERENCES ciclo_cuidado(id) ON DELETE CASCADE,
            trabalhador_id          INTEGER NOT NULL REFERENCES trabalhadores(id),
            medico_id               INTEGER REFERENCES funcionarios(id),

            estimativa_valor        INTEGER,
            estimativa_tipo         VARCHAR(20) CHECK (estimativa_tipo IN ('semanas', 'meses', 'sessoes')),
            data_estimativa_inicio  TIMESTAMP,
            data_estimativa_fim     TIMESTAMP,

            status                  VARCHAR(30) NOT NULL DEFAULT 'EM_TRATAMENTO'
                                    CHECK (status IN ('EM_TRATAMENTO', 'ALTA_MEDICA', 'ALTA_ADMINISTRATIVA', 'SUSPENSO', 'ABANDONOU')),
            data_alta               TIMESTAMP,
            medico_alta_id          INTEGER REFERENCES funcionarios(id),
            motivo_alta             TEXT,
            observacoes_alta        TEXT,

            criado_em               TIMESTAMP NOT NULL DEFAULT NOW(),
            atualizado_em           TIMESTAMP NOT NULL DEFAULT NOW(),
            criado_por              VARCHAR(255),
            atualizado_por          VARCHAR(255),

            UNIQUE (ciclo_id, trabalhador_id)
        )
    """)
    print("   ✅ Tabela criada (ou já existia).")

    # ─── 2. Criar índices ──────────────────────────────────────────────
    print("   → Criando índices...")
    for stmt in [
        "CREATE INDEX IF NOT EXISTS idx_pt_trabalhador ON paciente_tratamento(trabalhador_id)",
        "CREATE INDEX IF NOT EXISTS idx_pt_medico      ON paciente_tratamento(medico_id)",
        "CREATE INDEX IF NOT EXISTS idx_pt_status      ON paciente_tratamento(status)",
        "CREATE INDEX IF NOT EXISTS idx_pt_ciclo       ON paciente_tratamento(ciclo_id)",
    ]:
        cur.execute(stmt)
    print("   ✅ Índices criados.")

    # ─── 3. Migrar dados existentes (ciclos ativos) ────────────────────
    print("   → Migrando pacientes com ciclos ativos existentes...")
    cur.execute("""
        INSERT INTO paciente_tratamento (ciclo_id, trabalhador_id, medico_id, status, criado_por)
        SELECT
            cc.id,
            cc.trabalhador_id,
            cc.medico_alta_id,  -- usa o último médico registrado se houver
            'EM_TRATAMENTO',
            'MIGRAÇÃO_AUTOMATICA'
        FROM ciclo_cuidado cc
        WHERE cc.status = 'ATIVO'
        ON CONFLICT (ciclo_id, trabalhador_id) DO NOTHING
    """)
    migrados = cur.rowcount
    print(f"   ✅ {migrados} paciente(s) migrado(s) para paciente_tratamento.")

    # ─── 4. Verificação final ──────────────────────────────────────────
    cur.execute("SELECT COUNT(*) FROM paciente_tratamento")
    total = cur.fetchone()[0]
    print(f"\n📊 Total de registros em paciente_tratamento: {total}")

    conn.commit()
    print("\n✅ Migração concluída com sucesso!")

except Exception as e:
    conn.rollback()
    print(f"\n❌ ERRO durante migração: {e}")
    raise

finally:
    cur.close()
    conn.close()
