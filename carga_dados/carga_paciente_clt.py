import pandas as pd
import psycopg2

# =========================
# CONEXÃO COM O BANCO
# =========================
def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

# =========================
# LEITURA DO EXCEL
# =========================
df = pd.read_excel(
    r"C:\Users\williams.sobrinho\Downloads\MAPA_DE_TERCEIRIZADOS - NOVEMBRO 2025.xlsx"
)

print(df.columns.tolist())

# =========================
# CPF (IGUAL AO EXCEL)
# =========================
def limpa_cpf(cpf):
    if pd.isna(cpf):
        return None

    cpf_str = str(cpf).strip()

    if cpf_str.endswith(".0"):
        cpf_str = cpf_str[:-2]

    cpf_str = ''.join(filter(str.isdigit, cpf_str))

    if not cpf_str:
        return None

    return cpf_str.zfill(11)

# =========================
# DATA SEGURA (NaT → None)
# =========================
def data_ou_none(valor):
    data = pd.to_datetime(valor, errors="coerce")
    return None if pd.isna(data) else data

# =========================
# CARGA
# =========================
conn = get_connection()
cursor = conn.cursor()

try:
    for index, row in df.iterrows():

        cpf = limpa_cpf(row.get("CPF"))

        # 🚫 ignora CPF inválido
        if not cpf:
            print(f"Linha {index + 2} ignorada (CPF inválido)")
            continue

        # =========================
        # TRABALHADOR
        # =========================
        cursor.execute(
            "SELECT id FROM trabalhadores WHERE cpf = %s",
            (cpf,)
        )
        resultado = cursor.fetchone()

        if resultado:
            trabalhador_id = resultado[0]
        else:
            cursor.execute("""
                INSERT INTO trabalhadores (
                    nome_completo,
                    cpf
                ) VALUES (%s,%s)
                RETURNING id
            """, (
                row.get("NOME COMPLETO DO TERCEIRIZADO"),
                cpf
            ))
            trabalhador_id = cursor.fetchone()[0]

        # =========================
        # IDENTIFICADOR TÉCNICO
        # =========================
        numero_funcional = f"TERC-{cpf}"

        # =========================
        # EVITA VÍNCULO DUPLICADO
        # =========================
        cursor.execute("""
            SELECT 1
              FROM vinculos_trabalhadores
             WHERE trabalhador_id = %s
               AND numero_funcional = %s
        """, (
            trabalhador_id,
            numero_funcional
        ))

        if cursor.fetchone():
            print(f"Vínculo terceirizado já existe (CPF {cpf})")
            continue

        # =========================
        # INSERE VÍNCULO
        # =========================
        cursor.execute("""
            INSERT INTO vinculos_trabalhadores (
                trabalhador_id,
                numero_funcional,
                tipo_vinculo,
                especialidade,
                unidade_lotacao,
                data_admissao
            ) VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            trabalhador_id,
            numero_funcional,
            "TERCEIRIZADO",
            row.get("FUNÇÃO"),
            row.get("LOTAÇÃO"),
            data_ou_none(row.get("DATA DE ADMISSÃO"))
        ))

    conn.commit()
    print("✅ Carga de terceirizados realizada com sucesso")

except Exception as e:
    conn.rollback()
    print("❌ Erro na carga de terceirizados:", e)

finally:
    cursor.close()
    conn.close()
