# Documentação de arquitetura

## Visão Geral
O sistema é dividido em front-end (HTML/Tailwind/JS), back-end (Flask/Python), banco de dados (SQL) e infraestrutura de deploy (Docker).

- O front-end consome APIs REST do back-end.
- O back-end segue boas práticas de modularização (blueprints, services, models).
- O banco de dados é versionado via migrations.
- O deploy é feito via Docker Compose.

## Estrutura de Pastas
Veja README.md para detalhes.
