import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

# Lê o Excel
df = pd.read_excel(
    r"C:\Users\williams.sobrinho\ANALISE PROF QUALIVIDA\QUALIVIDA_CRUZADO_FOLHA_SGP.xlsx"
)

# Renomeia colunas do Excel para o padrão do banco
df = df.rename(columns={
    "NOME": "nome",
    "CPF": "cpf",
    "MATRICULA SGP": "num_func_num_vinc",
    "DATA NASCIMENTO": "data_nascimento",
    "CARGO": "especialidade",
    "E-MAIL": "email",
    "FONE": "telefone",
    "UNIDADE": "unidade_atendimento"
})

# Mantém somente as colunas usadas no INSERT
df = df[
    [
        "nome",
        "cpf",
        "num_func_num_vinc",
        "data_nascimento",
        "especialidade",
        "email",
        "telefone",
        "unidade_atendimento"
    ]
]

# Limpezas
df["cpf"] = df["cpf"].astype(str).str.replace(r"\D", "", regex=True)

df["data_nascimento"] = pd.to_datetime(
    df["data_nascimento"],
    errors="coerce",
    dayfirst=True
).dt.date

# Substitui NaN por None
df = df.where(pd.notnull(df), None)

# Conexão PostgreSQL
conn = psycopg2.connect(
    host="10.24.59.104",
    user="qualisus",
    password="h5eXAx59gJ3h84Xa",
    database="qualisus"
)

cursor = conn.cursor()

sql = """
INSERT INTO funcionarios
(nome, cpf, num_func_num_vinc, data_nascimento, especialidade, email, telefone, unidade_atendimento)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
"""

cursor.executemany(sql, df.values.tolist())
conn.commit()

cursor.close()
conn.close()

print("✅ Carga finalizada com sucesso!")
