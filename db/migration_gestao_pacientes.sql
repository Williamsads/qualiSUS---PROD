-- =============================================================
-- MIGRAÇÃO: Módulo Gestão de Pacientes (paciente_tratamento)
-- QualiSUS v1.7.0 | Ciclo Clínico Completo
-- =============================================================

-- Tabela principal de tratamento (vinculada ao ciclo_cuidado)
CREATE TABLE IF NOT EXISTS paciente_tratamento (
    id                      SERIAL PRIMARY KEY,
    ciclo_id                INTEGER NOT NULL REFERENCES ciclo_cuidado(id) ON DELETE CASCADE,
    trabalhador_id          INTEGER NOT NULL REFERENCES trabalhadores(id),
    medico_id               INTEGER REFERENCES funcionarios(id),

    -- Estimativa de Tratamento
    estimativa_valor        INTEGER,
    estimativa_tipo         VARCHAR(20) CHECK (estimativa_tipo IN ('semanas', 'meses', 'sessoes')),
    data_estimativa_inicio  TIMESTAMP,
    data_estimativa_fim     TIMESTAMP,

    -- Alta Médica
    status                  VARCHAR(30) NOT NULL DEFAULT 'EM_TRATAMENTO'
                            CHECK (status IN ('EM_TRATAMENTO', 'ALTA_MEDICA', 'ALTA_ADMINISTRATIVA', 'SUSPENSO', 'ABANDONOU')),
    data_alta               TIMESTAMP,
    medico_alta_id          INTEGER REFERENCES funcionarios(id),
    motivo_alta             TEXT,
    observacoes_alta        TEXT,

    -- Auditoria
    criado_em               TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em           TIMESTAMP NOT NULL DEFAULT NOW(),
    criado_por              VARCHAR(255),
    atualizado_por          VARCHAR(255),

    -- Garante unicidade: um paciente só tem um registro ativo por ciclo
    UNIQUE (ciclo_id, trabalhador_id)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_pt_trabalhador ON paciente_tratamento(trabalhador_id);
CREATE INDEX IF NOT EXISTS idx_pt_medico      ON paciente_tratamento(medico_id);
CREATE INDEX IF NOT EXISTS idx_pt_status      ON paciente_tratamento(status);
CREATE INDEX IF NOT EXISTS idx_pt_ciclo       ON paciente_tratamento(ciclo_id);

-- Insere registros para pacientes já em ciclo ativo (migração de dados existentes)
INSERT INTO paciente_tratamento (ciclo_id, trabalhador_id, medico_id, status, criado_por)
SELECT 
    cc.id,
    cc.trabalhador_id,
    NULL,
    'EM_TRATAMENTO',
    'MIGRAÇÃO_AUTOMATICA'
FROM ciclo_cuidado cc
WHERE cc.status = 'ATIVO'
ON CONFLICT (ciclo_id, trabalhador_id) DO NOTHING;

-- Comentários de documentação
COMMENT ON TABLE paciente_tratamento IS 'Ciclo clínico de tratamento: estimativa e alta médica. Não deletar registros – apenas alterar status.';
COMMENT ON COLUMN paciente_tratamento.estimativa_tipo IS 'Unidade da estimativa: semanas, meses ou sessoes';
COMMENT ON COLUMN paciente_tratamento.data_estimativa_fim IS 'Calculado automaticamente com base em estimativa_valor + estimativa_tipo';
COMMENT ON COLUMN paciente_tratamento.status IS 'EM_TRATAMENTO -> ALTA_MEDICA/ALTA_ADMINISTRATIVA/SUSPENSO/ABANDONOU';
