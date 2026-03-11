-- =========================================
-- SCRIPT: Limpeza de Dados de Pacientes com Backup
-- Sistema: QualiVida / QualiSUS (PostgreSQL)
-- Data: 2026-03-09
-- =========================================

-- 1. Criação das Tabelas de Backup
-- O prefixo 'backup_20260309_' identifica a data da operação
CREATE TABLE backup_20260309_trabalhadores AS SELECT * FROM trabalhadores;
CREATE TABLE backup_20260309_vinculos_trabalhadores AS SELECT * FROM vinculos_trabalhadores;
CREATE TABLE backup_20260309_agendamento_exames AS SELECT * FROM agendamento_exames;
CREATE TABLE backup_20260309_ciclo_cuidado AS SELECT * FROM ciclo_cuidado;
CREATE TABLE backup_20260309_tratamentos AS SELECT * FROM tratamentos;
CREATE TABLE backup_20260309_desfechos_clinicos AS SELECT * FROM desfechos_clinicos;
CREATE TABLE backup_20260309_desfecho_logs AS SELECT * FROM desfecho_logs;
CREATE TABLE backup_20260309_paciente_tratamento AS SELECT * FROM paciente_tratamento;
CREATE TABLE backup_20260309_ppp AS SELECT * FROM ppp;
CREATE TABLE backup_20260309_ppp_lotacao AS SELECT * FROM ppp_lotacao;
CREATE TABLE backup_20260309_ppp_profissiografia AS SELECT * FROM ppp_profissiografia;
CREATE TABLE backup_20260309_ppp_responsaveis AS SELECT * FROM ppp_responsaveis_registros;
CREATE TABLE backup_20260309_ppp_ambientais AS SELECT * FROM ppp_registros_ambientais;
CREATE TABLE backup_20260309_ppp_historico AS SELECT * FROM ppp_historico;

-- 2. Limpeza dos Dados (Deleção em Cascata)
-- O comando TRUNCATE com CASCADE esvaziará automaticamente todas as tabelas
-- que dependem de trabalhadores e ppp via chaves estrangeiras (ex: agendamento_exames)
-- A opção RESTART IDENTITY reseta as sequências (auto_increment/serial)
TRUNCATE TABLE 
    trabalhadores, 
    ppp 
RESTART IDENTITY CASCADE;

-- 3. Validação dos Dados Restantes (Geração de Relatório de Limpeza)
-- Deverá retornar 0 nas tabelas limpas e valores > 0 nos usuários e médicos
SELECT 
  'Trabalhadores (Pacientes)' as tabela, COUNT(*) as registros_restantes, '0' as esperado FROM trabalhadores
UNION ALL
SELECT 'Desfechos Clínicos', COUNT(*), '0' FROM desfechos_clinicos
UNION ALL
SELECT 'Agendamentos/Exames', COUNT(*), '0' FROM agendamento_exames
UNION ALL
SELECT 'Emissão de PPPs', COUNT(*), '0' FROM ppp
UNION ALL
SELECT 'Usuários (Sistema)', COUNT(*), '>0' FROM usuarios
UNION ALL
SELECT 'Funcionários (Médicos)', COUNT(*), '>0' FROM funcionarios;
