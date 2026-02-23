
-- Migration: Decouple PPP from servidores table
-- Adding manual worker fields and removing servidor_id

-- 1. Add new columns
ALTER TABLE ppp ADD COLUMN nome_trabalhador VARCHAR(255);
ALTER TABLE ppp ADD COLUMN cpf_trabalhador VARCHAR(20);
ALTER TABLE ppp ADD COLUMN data_nascimento DATE;
ALTER TABLE ppp ADD COLUMN sexo CHAR(1);
ALTER TABLE ppp ADD COLUMN matricula_trabalhador VARCHAR(50);
ALTER TABLE ppp ADD COLUMN cargo_trabalhador VARCHAR(255);
ALTER TABLE ppp ADD COLUMN unidade_trabalhador VARCHAR(255);

-- 2. Optional: Migrate existing data if possible (best effort)
-- UPDATE ppp p
-- SET nome_trabalhador = t.nome_completo,
--     cpf_trabalhador = t.cpf,
--     data_nascimento = t.data_nascimento,
--     -- sexo = t.sexo, -- t.sexo doesn't exist as seen before
--     matricula_trabalhador = v.numero_funcional,
--     unidade_trabalhador = v.unidade_lotacao
-- FROM trabalhadores t
-- LEFT JOIN vinculos_trabalhadores v ON v.trabalhador_id = t.id
-- WHERE p.servidor_id = t.id;

-- 3. Remove foreign key constraint and column
-- Find constraint name first if needed, but usually it's ppp_servidor_id_fkey
ALTER TABLE ppp DROP CONSTRAINT IF EXISTS ppp_servidor_id_fkey;
ALTER TABLE ppp DROP COLUMN servidor_id;
