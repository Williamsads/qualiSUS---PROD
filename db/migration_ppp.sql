-- =============================================================
-- MIGRAÇÃO: Módulo Gestão de PPP
-- QualiSUS v1.8.0 | Gestão de Perfil Profissiográfico
-- =============================================================

-- Tabela principal de PPP
CREATE TABLE IF NOT EXISTS ppp (
    id                      SERIAL PRIMARY KEY,
    servidor_id            INTEGER NOT NULL REFERENCES trabalhadores(id),
    unidade_id              INTEGER REFERENCES unidades_saude(id), -- Ajuste para o nome correto da tabela
    
    -- Status: ELABORACAO, FINALIZADO, ASSINADO
    status                  VARCHAR(30) NOT NULL DEFAULT 'ELABORACAO'
                            CHECK (status IN ('ELABORACAO', 'FINALIZADO', 'ASSINADO')),
    
    -- Dados de Emissão e Assinatura
    data_emissao            DATE,
    rep_legal_nome          VARCHAR(255),
    rep_legal_cpf           VARCHAR(14),
    observacoes              TEXT,
    
    -- Auditoria e Controle
    criado_por              INTEGER REFERENCES usuarios(id),
    data_criacao            TIMESTAMP NOT NULL DEFAULT NOW(),
    finalizado_por          INTEGER REFERENCES usuarios(id),
    data_finalizacao        TIMESTAMP,
    assinado_por            INTEGER REFERENCES usuarios(id),
    data_assinatura         TIMESTAMP,
    
    arquivo_pdf             VARCHAR(255),
    ativo                   BOOLEAN DEFAULT TRUE
);

-- Aba 2: Lotação e Atribuição
CREATE TABLE IF NOT EXISTS ppp_lotacao (
    id                      SERIAL PRIMARY KEY,
    ppp_id                  INTEGER NOT NULL REFERENCES ppp(id) ON DELETE CASCADE,
    periodo_inicio         DATE,
    periodo_fim            DATE,
    cnpj                    VARCHAR(18),
    setor                   VARCHAR(255),
    cargo                   VARCHAR(255),
    funcao                  VARCHAR(255),
    cbo                     VARCHAR(10),
    gfip                    VARCHAR(10)
);

-- Aba 3: Profissiografia
CREATE TABLE IF NOT EXISTS ppp_profissiografia (
    id                      SERIAL PRIMARY KEY,
    ppp_id                  INTEGER NOT NULL REFERENCES ppp(id) ON DELETE CASCADE,
    periodo_inicio         DATE,
    periodo_fim            DATE,
    descricao               TEXT
);

-- Aba 4: Registros Ambientais
CREATE TABLE IF NOT EXISTS ppp_registros_ambientais (
    id                      SERIAL PRIMARY KEY,
    ppp_id                  INTEGER NOT NULL REFERENCES ppp(id) ON DELETE CASCADE,
    periodo_inicio         DATE, -- Período simplificado
    periodo_fim            DATE,
    tipo                    VARCHAR(50), -- Físico, Químico, Biológico
    fator_risco             VARCHAR(255),
    intensidade             VARCHAR(255),
    tecnica                 VARCHAR(255),
    epc_eficaz              BOOLEAN,
    epi_eficaz              BOOLEAN,
    ca_epi                  VARCHAR(20)
);

-- Aba 5: Responsáveis pelos Registros
CREATE TABLE IF NOT EXISTS ppp_responsaveis_registros (
    id                      SERIAL PRIMARY KEY,
    ppp_id                  INTEGER NOT NULL REFERENCES ppp(id) ON DELETE CASCADE,
    periodo_inicio         DATE,
    periodo_fim            DATE,
    cpf                     VARCHAR(14),
    registro_conselho       VARCHAR(50),
    nome                    VARCHAR(255)
);

-- Histórico de Auditoria
CREATE TABLE IF NOT EXISTS ppp_historico (
    id                      SERIAL PRIMARY KEY,
    ppp_id                  INTEGER NOT NULL REFERENCES ppp(id) ON DELETE CASCADE,
    usuario_id              INTEGER REFERENCES usuarios(id),
    acao                    VARCHAR(100), -- Criado, Editado, Finalizado, Assinado, PDF Gerado
    descricao               TEXT,
    data                    TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_ppp_servidor ON ppp(servidor_id);
CREATE INDEX IF NOT EXISTS idx_ppp_status   ON ppp(status);
CREATE INDEX IF NOT EXISTS idx_ppp_hist_ppp  ON ppp_historico(ppp_id);

COMMENT ON TABLE ppp IS 'Registro mestre de PPP';
COMMENT ON TABLE ppp_historico IS 'Log de auditoria do PPP';
